"""
This module implements the Language Server Protocol for Go using gopls.
"""

import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
import pathlib
import pwd
import shutil
import subprocess
from typing import AsyncIterator, Dict, Any
from ...language_server import LanguageServer
from ...multilspy_config import MultilspyConfig
from ...multilspy_logger import MultilspyLogger
from ...lsp_protocol_handler.server import ProcessLaunchInfo
from ...lsp_protocol_handler.lsp_types import InitializeParams
from ...multilspy_utils import PlatformUtils, PlatformId

import sys

class GoplsServer(LanguageServer):
    """
    Implementation of the Language Server Protocol for Go using gopls.
    """

    def __init__(self, config: MultilspyConfig, logger: MultilspyLogger, repository_root_path: str):
        """
        Creates a GoplsServer instance. This class is not meant to be instantiated directly. Use LanguageServer.create() instead.
        """
        gopls_executable_path = self.setup_runtime_dependencies(logger, config)
        # Construct full command with args
        #cmd = f"{gopls_executable_path} serve --stdio"
        #cmd = f"{gopls_executable_path} serve -listen=127.0.0.1:37375"
        cmd = f"{gopls_executable_path} serve"
        super().__init__(
            config,
            logger,
            repository_root_path,
            ProcessLaunchInfo(cmd=cmd, cwd=repository_root_path),
            "go"
        )
        self.server_ready = asyncio.Event()

    def setup_runtime_dependencies(self, logger: MultilspyLogger, config: MultilspyConfig) -> str:
        """
        Setup runtime dependencies for gopls Language Server.
        Verifies that Go is installed and installs gopls if needed.
        
        :param logger: The logger to use
        :param config: The Multilspy configuration
        :return: Path to the gopls executable
        :raises: RuntimeError if Go is not installed or if platform is not supported
        """
        platform_id = PlatformUtils.get_platform_id()

        valid_platforms = [
            PlatformId.LINUX_x64,
            PlatformId.LINUX_arm64,
            PlatformId.OSX,
            PlatformId.OSX_x64,
            PlatformId.OSX_arm64,
            PlatformId.WIN_x64,
            PlatformId.WIN_arm64,
        ]
        assert platform_id in valid_platforms, f"Platform {platform_id} is not supported for multilspy Go at the moment"

        # Verify Go is installed
        go_path = shutil.which('go')
        if not go_path:
            error_msg = "Go is not installed. Please install Go from https://golang.org/doc/install"
            logger.log(error_msg, logging.ERROR)
            raise RuntimeError(error_msg)

        # Check for gopls in both PATH and Go binary directory
        gopls_path = shutil.which("gopls")
        if not gopls_path:
            # Check in Go binary path
            home = os.path.expanduser("~")
            go_bin_path = os.path.join(home, "go", "bin")
            gopls_binary = "gopls.exe" if os.name == "nt" else "gopls"
            potential_gopls_path = os.path.join(go_bin_path, gopls_binary)
            
            if os.path.exists(potential_gopls_path) and os.access(potential_gopls_path, os.X_OK):
                gopls_path = potential_gopls_path
                logger.log(f"Found gopls in Go binary path: {gopls_path}", logging.INFO)
            else:
                # Try installing gopls
                logger.log("Installing gopls...", logging.INFO)
                try:
                    install_cmd = ["go", "install", "golang.org/x/tools/gopls@latest"]
                    result = subprocess.run(install_cmd, check=True, capture_output=True, text=True)
                    logger.log("gopls installation completed", logging.INFO)
                    
                    # After installation, check Go binary path first
                    if os.path.exists(potential_gopls_path) and os.access(potential_gopls_path, os.X_OK):
                        gopls_path = potential_gopls_path
                        logger.log(f"Using newly installed gopls from: {gopls_path}", logging.INFO)
                    else:
                        gopls_path = shutil.which("gopls")
                        
                except subprocess.CalledProcessError as e:
                    error_msg = f"Failed to install gopls: {e.stderr}"
                    logger.log(error_msg, logging.ERROR)
                    raise RuntimeError(error_msg)

        if not gopls_path:
            error_msg = "gopls installation failed. Please install gopls manually using 'go install golang.org/x/tools/gopls@latest'"
            logger.log(error_msg, logging.ERROR)
            raise RuntimeError(error_msg)

        print(f"Using gopls at: {gopls_path}")
        logger.log(f"Using gopls at: {gopls_path}", logging.INFO)
        #return gopls_path
        return "gopls"

    def _get_initialize_params(self, repository_absolute_path: str) -> Dict[str, Any]:
        """
        Returns the initialize params for the Go Language Server (gopls).
        
        :param repository_absolute_path: The absolute path to the repository root
        :return: Dictionary containing the server initialization parameters
        """
        with open(os.path.join(os.path.dirname(__file__), "initialize_params.json"), "r") as f:
            params = json.load(f)
            del params["_description"]

        # Fix processId to be an actual number
        params["processId"] = os.getpid()
        params["rootPath"] = repository_absolute_path
        params["rootUri"] = pathlib.Path(repository_absolute_path).as_uri()
        # params["workspaceFolders"][0]["uri"] = pathlib.Path(repository_absolute_path).as_uri()
        # params["workspaceFolders"][0]["name"] = os.path.basename(repository_absolute_path)

        return params

    @asynccontextmanager
    async def start_server(self) -> AsyncIterator["GoplsServer"]:
        """
        Starts the Go Language Server (gopls), waits for the server to be ready and yields the LanguageServer instance.

        Usage:
        ```
        async with lsp.start_server():
            # LanguageServer has been initialized and ready to serve requests
            await lsp.request_definition(...)
            await lsp.request_references(...)
            # Shutdown the LanguageServer on exit from scope
        # LanguageServer has been shutdown
        ```
        """
        async def register_capability_handler(params):
            assert "registrations" in params
            for registration in params["registrations"]:
                if registration["method"] == "workspace/executeCommand":
                    # gopls supports various commands like 'gopls.add_dependency'
                    pass
            return

        async def execute_client_command_handler(params):
            return []

        async def do_nothing(params):
            print(f"Received message: {params}")
            return

        async def window_log_message(msg):
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        async def window_show_message(msg):
            self.logger.log(f"LSP: window/showMessage: {msg}", logging.INFO)

        self.server.on_request("client/registerCapability", register_capability_handler)
        self.server.on_notification("language/status", do_nothing)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_request("workspace/executeClientCommand", execute_client_command_handler)
        self.server.on_notification("$/progress", do_nothing)
        self.server.on_notification("textDocument/publishDiagnostics", do_nothing)
        self.server.on_notification("language/actionableNotification", do_nothing)
        self.server.on_notification("textDocument/completion", do_nothing)
        self.server.on_notification("textDocument/implementation", do_nothing)

        # Start gopls in server mode
        async with super().start_server():
            self.logger.log("Starting gopls server process", logging.INFO)
            await self.server.start()
            initialize_params = self._get_initialize_params(self.repository_root_path)

            self.logger.log(
                "Sending initialize request from LSP client to LSP server and awaiting response",
                logging.INFO,
            )
            try:
                init_response = await self.server.send.initialize(initialize_params)
            except TimeoutError as e:
                self.logger.log(f"Timeout during initialization: {str(e)}", logging.ERROR)
                raise
            except Exception as e:
                self.logger.log(f"Error during initialization: {str(e)}", logging.ERROR)
                raise
            
            # Verify basic gopls capabilities without making strict assertions
            if "textDocumentSync" not in init_response["capabilities"]:
                self.logger.log("Warning: gopls server does not support textDocumentSync", logging.WARNING)
            if "completionProvider" not in init_response["capabilities"]:
                self.logger.log("Warning: gopls server does not support completions", logging.WARNING)
            else:
                self.completions_available.set()
            
            self.server.notify.initialized({})

            # gopls is typically ready after initialization
            self.server_ready.set()

            yield self

            await self.server.shutdown()
            await self.server.stop()

    async def register_capability_handler(self, params):
        return
