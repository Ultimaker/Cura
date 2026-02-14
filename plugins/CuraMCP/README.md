# Cura MCP Server Plugin

This plugin exposes a Model Context Protocol (MCP) server within Ultimaker Cura, allowing AI agents (like Claude Desktop or other MCP clients) to inspect and control the Cura UI and 3D scene.

## Installation

1.  Locate your Cura configuration directory.
    -   **Windows**: `%APPDATA%\cura\<version>\plugins`
    -   **macOS**: `~/Library/Application Support/cura/<version>/plugins`
    -   **Linux**: `~/.local/share/cura/<version>/plugins`
2.  Copy the `CuraMCP` folder into the `plugins` directory.
3.  Restart Cura.

## Usage

Once installed and Cura is running, the MCP server will start automatically. By default, it listens on `stdio` or a configured transport (check plugin settings if applicable).

To connect an MCP client (e.g., Claude Desktop):

1.  Configure your MCP client to launch Cura with the plugin enabled, or connect to the running instance if supported.
2.  Ensure the environment variables or command-line arguments are set correctly for the MCP connection.

## Available Tools

The following tools are available for AI agents to interact with Cura:

### UI Inspection & Control
-   `get_ui_tree()`: Returns a hierarchical JSON representation of the current UI state, including visible elements and their properties.
-   `click_element(id)`: Simulates a click on a UI element identified by its unique `id`.
-   `set_value(id, value)`: Sets the value of a UI element (e.g., a text field or slider) identified by `id`.
-   `invoke_action(id)`: Triggers the default action associated with a UI element identified by `id`.

### Camera Control
-   `camera_home()`: Resets the camera to the default home position.
-   `camera_set_view(view)`: Sets the camera to a predefined view (e.g., "top", "front", "right", "perspective").
-   `camera_look_at(x, y, z)`: Points the camera at a specific coordinate in 3D space.

### Tool Management
-   `tool_set_active(tool_id)`: Activates a specific tool (e.g., "Translate", "Rotate", "Scale") by its ID.
-   `tool_get_active()`: Returns the ID of the currently active tool.

### Selection Management
-   `selection_get()`: Returns a list of IDs for the currently selected objects in the scene.
-   `selection_clear()`: Deselects all objects.
-   `selection_set(node_ids)`: Selects the objects specified by the list of `node_ids`.

## Development

To run tests for this plugin:

1.  Ensure you have the development dependencies installed.
2.  Navigate to the plugin directory:
    ```bash
    cd Cura/plugins/CuraMCP
    ```
3.  Run the tests using `pytest`:
    ```bash
    pytest tests/
    ```
