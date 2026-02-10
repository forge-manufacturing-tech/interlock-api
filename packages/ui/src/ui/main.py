import os
from dataclasses import field
from typing import Any

import rio

# Import generated client
from api_client import Client
from api_client.api.default import (
    ask_agent_agent_ask_post,
    ingest_bom_ingest_bom_post,
    read_root_get,
)
from api_client.models.body_ingest_bom_ingest_bom_post import (
    BodyIngestBomIngestBomPost,
)
from api_client.types import File

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")


class Root(rio.Component):
    """
    Main application component with sidebar navigation and content area.
    """

    active_page: str = "Home"

    # API Client
    _client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = Client(base_url=API_URL)
        return self._client

    # --- State: Home ---
    system_status: str = "Checking..."
    status_color: str | rio.Color = "grey"

    # --- State: BOM Ingestion ---
    ingestion_result: str = ""
    preview_data: list[Any] = field(default_factory=list)
    is_ingesting: bool = False

    # --- State: Agent ---
    agent_history: list[tuple[str, str]] = field(
        default_factory=list
    )  # List of (Question, Answer)
    agent_input: str = ""
    is_agent_thinking: bool = False

    async def on_mount(self):
        """Check system status on load."""
        await self.check_status()

    async def check_status(self):
        self.status_color = "grey"
        try:
            # The generated sync endpoint returns the parsed response model directly
            # or None on error if not raising. sync_detailed returns Response object.
            # We used asyncio method.
            response = await read_root_get.asyncio(client=self.client)
            if response:
                # It returns a dict according to the API, but generated client might verify schemas if defined.
                # The API returns {"system": "Interlock OS", "status": "online"}
                if isinstance(response, dict) or hasattr(response, "get"):
                    # Handle both dict and potentially model if generated differently
                    status = (
                        response.get("status")
                        if isinstance(response, dict)
                        else getattr(response, "status", "Unknown")
                    )
                    sys_name = (
                        response.get("system")
                        if isinstance(response, dict)
                        else getattr(response, "system", "System")
                    )

                    self.system_status = f"{sys_name} is {status}"
                    self.status_color = "green" if status == "online" else "red"
                else:
                    self.system_status = str(response)
                    self.status_color = "green"
            else:
                self.system_status = "Offline"
                self.status_color = "red"
        except Exception as e:
            self.system_status = f"Connection Error: {e}"
            self.status_color = "red"

    async def on_file_upload(self, event: rio.FilePickEvent):
        """Handle BOM file upload."""
        if not event.file:
            return

        self.is_ingesting = True
        self.ingestion_result = "Uploading..."

        try:
            content = await event.file.read_bytes()

            from io import BytesIO

            file_payload = BytesIO(content)

            bom_body = BodyIngestBomIngestBomPost(
                file=File(
                    payload=file_payload,
                    file_name=event.file.name,
                    mime_type=event.file.media_type or "text/csv",
                )
            )

            response = await ingest_bom_ingest_bom_post.asyncio(
                client=self.client, body=bom_body
            )

            if response:
                filename = (
                    response.get("filename")
                    if isinstance(response, dict)
                    else getattr(response, "filename", "File")
                )
                rows_count = (
                    response.get("rows")
                    if isinstance(response, dict)
                    else getattr(response, "rows", 0)
                )

                self.ingestion_result = f"Ingested {rows_count} rows from {filename}"
                self.preview_data = (
                    response.get("preview", [])
                    if isinstance(response, dict)
                    else getattr(response, "preview", [])
                )
            else:
                self.ingestion_result = "Failed to ingest (No response)"

        except Exception as e:
            self.ingestion_result = f"Error: {e}"
        finally:
            self.is_ingesting = False

    async def on_agent_ask(self):
        """Ask the agent a question."""
        if not self.agent_input.strip():
            return

        question = self.agent_input
        self.agent_input = ""  # Clear input
        self.is_agent_thinking = True

        try:
            response = await ask_agent_agent_ask_post.asyncio(
                client=self.client, question=question
            )

            if response and (isinstance(response, dict) or hasattr(response, "get")):
                answer = (
                    response.get("answer")
                    if isinstance(response, dict)
                    else getattr(response, "answer", "No answer provided.")
                )
            else:
                answer = str(response)

            self.agent_history.append((question, answer))

        except Exception as e:
            self.agent_history.append((question, f"Error: {e}"))
        finally:
            self.is_agent_thinking = False

    def build_sidebar(self) -> rio.Component:
        def set_page(page: str):
            self.active_page = page

        def nav_button(text: str, page: str, icon: str):
            is_active = self.active_page == page
            return rio.Button(
                content=rio.Row(rio.Icon(icon), rio.Text(text), spacing=1, align_y=0.5),
                style="major" if is_active else "plain-text",
                on_press=lambda: set_page(page),
            )

        return rio.Column(
            rio.Text("Interlock", style="heading1", margin_bottom=2, justify="center"),
            nav_button("Home", "Home", "material/home"),
            nav_button("Ingestion", "Ingestion", "material/cloud_upload"),
            nav_button("Agent", "Agent", "material/smart_toy"),
            rio.Spacer(),
            rio.Row(
                rio.Icon("material/info", fill="dim"),
                rio.Text("v0.1.0", style="dim"),
                spacing=0.5,
                align_x=0.5,
            ),
            spacing=1,
            min_width=18,
            margin=2,
        )

    def build_home_page(self) -> rio.Component:
        icon_fill = (
            self.status_color
            if isinstance(self.status_color, (str, rio.Color))
            else "grey"
        )

        return rio.Column(
            rio.Text("Dashboard", style="heading1", margin_bottom=1),
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon(
                            "material/dns", fill=icon_fill, min_width=2, min_height=2
                        ),
                        rio.Text("System Status", style="heading3"),
                        spacing=1,
                        align_y=0.5,
                    ),
                    rio.Separator(),
                    rio.Text(self.system_status, style="text", justify="center"),
                    spacing=1,
                    margin=2,
                ),
                color="neutral",
            ),
            rio.Button(
                "Refresh Status", icon="material/refresh", on_press=self.check_status
            ),
            spacing=2,
            margin=2,
            align_x=0.5,
        )

    def build_ingestion_page(self) -> rio.Component:
        preview_comp = rio.Column()
        if self.preview_data:
            rows = []
            for item in self.preview_data:
                rows.append(rio.Card(rio.Text(str(item)), margin_bottom=0.5))

            preview_comp = rio.Column(
                rio.Text("Preview Data", style="heading2"), *rows, spacing=1
            )

        return rio.Column(
            rio.Text("BOM Ingestion", style="heading1", margin_bottom=1),
            rio.Text(
                "Upload your Bill of Materials (CSV/Excel) below to process manufacturing data."
            ),
            rio.Card(
                rio.FilePickerArea(
                    on_pick_file=self.on_file_upload,
                    content=rio.Column(
                        rio.Icon(
                            "material/cloud_upload",
                            min_width=5,
                            min_height=5,
                            fill="primary",
                        ),
                        rio.Text("Drag & Drop or Click to Upload", style="heading3"),
                        rio.Text("Supported formats: .csv, .xlsx", style="dim"),
                        align_x=0.5,
                        align_y=0.5,
                        spacing=1,
                    ),
                    min_height=20,
                ),
                color="neutral",
            ),
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon("material/info", fill="primary"),
                        rio.Text("Status", style="heading3"),
                        spacing=1,
                    ),
                    rio.Text(
                        self.ingestion_result
                        if self.ingestion_result
                        else "Waiting for file..."
                    ),
                    spacing=1,
                    margin=1,
                ),
                color="primary" if self.is_ingesting else "neutral",
            ),
            preview_comp,
            spacing=2,
            margin=2,
            grow_x=True,
        )

    def build_agent_page(self) -> rio.Component:
        history_items = []
        for q, a in self.agent_history:
            # User Message
            history_items.append(
                rio.Row(
                    rio.Spacer(),
                    rio.Card(
                        rio.Text(q, style="text"),
                        color="primary",
                        margin_left=4,
                    ),
                    spacing=1,
                )
            )
            # Agent Message
            history_items.append(
                rio.Row(
                    rio.Icon(
                        "material/smart_toy",
                        min_width=2,
                        min_height=2,
                        fill="secondary",
                        align_y=0,
                    ),
                    rio.Card(
                        rio.Markdown(a),
                        color="neutral",
                        margin_right=4,
                    ),
                    spacing=1,
                )
            )

        return rio.Column(
            rio.Text("AI Agent", style="heading1"),
            rio.Text("Ask questions about your manufacturing data or supply chain."),
            rio.ScrollContainer(
                rio.Column(*history_items, spacing=1)
                if history_items
                else rio.Text("No messages yet.", style="dim", justify="center"),
                grow_y=True,
                scroll_y="auto",
                # min_height=30, # Let it grow
            ),
            rio.Card(
                rio.Row(
                    rio.TextInput(
                        text=self.agent_input,
                        on_change=lambda t: setattr(self, "agent_input", t),
                        label="Ask something...",
                        grow_x=True,
                        on_confirm=lambda _: self.on_agent_ask(),
                    ),
                    rio.Button(
                        "Send",
                        icon="material/send",
                        on_press=self.on_agent_ask,
                        is_loading=self.is_agent_thinking,
                        style="major",
                    ),
                    spacing=1,
                    align_y=0.5,
                    margin=1,
                ),
                color="neutral",
                margin_top=1,
            ),
            spacing=1,
            margin=2,
            grow_y=True,
        )

    def build(self) -> rio.Component:
        content = rio.Text("Page not found")

        if self.active_page == "Home":
            content = self.build_home_page()
        elif self.active_page == "Ingestion":
            content = self.build_ingestion_page()
        elif self.active_page == "Agent":
            content = self.build_agent_page()

        # Wrap content
        # For agent page, we want full height for chat, so handle layout carefully
        # Simple container for all pages is fine

        main_area = rio.Container(content, grow_x=True, grow_y=True, margin=2)

        return rio.Row(
            self.build_sidebar(),
            rio.Separator(),
            main_area,
            min_height=0,  # Allow filling screen
            grow_y=True,
        )


app = rio.App(build=Root)

if __name__ == "__main__":
    app.run_in_browser()
