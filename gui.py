import pathlib
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import logging

import customtkinter as ctk
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

API_BASE = "http://localhost:8000/api"
MAX_FILES = 10
DEFAULT_TOP_K = 5

PALETTE = {
    "bg": "#0d0f14",
    "surface": "#161b27",
    "card": "#1e2535",
    "border": "#263047",
    "accent": "#4f8ef7",
    "accent_hover": "#6aa0ff",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#f87171",
    "text": "#ffffff",
    "muted": "#cbd5e1",
    "pending": "#fbbf24",
    "processing": "#60a5fa",
    "ready": "#34d399",
}


STATUS_COLORS = {
    "PENDING": PALETTE["pending"],
    "PROCESSING": PALETTE["processing"],
    "READY": PALETTE["success"],
    "ERROR": PALETTE["error"],
}


class RagApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RAG Research Engine")
        self.geometry("1280x820")
        self.minsize(1000, 700)
        self.configure(fg_color=PALETTE["bg"])
        self._configure_fonts()

        self._local_files: list[pathlib.Path] = []
        self._remote_docs: list[dict] = []
        self._query_in_progress = False
        self._query_answer = ""
        self._upload_in_progress = False

        self._build_ui()
        self._start_refresh_loop()

    def _configure_fonts(self):
        self.font_title = ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        self.font_body = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_mono = ctk.CTkFont(family="Consolas", size=11)
        self.font_small = ctk.CTkFont(family="Segoe UI", size=11)
        self.font_badge = ctk.CTkFont(family="Segoe UI", size=10, weight="bold")

    def _build_ui(self):
        self._build_header()
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        content.columnconfigure(0, weight=5)
        content.columnconfigure(1, weight=4)
        content.rowconfigure(0, weight=1)

        self._build_left_panel(content)
        self._build_right_panel(content)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PALETTE["surface"], corner_radius=0, height=64)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=0)

        logo_frame = ctk.CTkFrame(inner, fg_color="transparent")
        logo_frame.pack(side="left", fill="y")

        dot = ctk.CTkFrame(logo_frame, width=10, height=10,
                           fg_color=PALETTE["accent"], corner_radius=5)
        dot.pack(side="left", padx=(0, 10), pady=27)

        title = ctk.CTkLabel(logo_frame, text="RAG Research Engine",
                             font=self.font_title, text_color="#ffffff")
        title.pack(side="left", pady=0)

        status_frame = ctk.CTkFrame(inner, fg_color="transparent")
        status_frame.pack(side="right", fill="y")

        self.status_dot = ctk.CTkFrame(status_frame, width=8, height=8,
                                       fg_color=PALETTE["muted"], corner_radius=4)
        self.status_dot.pack(side="left", padx=(0, 6), pady=28)

        self.api_status_label = ctk.CTkLabel(status_frame, text="Connecting...",
                                              font=self.font_small, text_color=PALETTE["muted"])
        self.api_status_label.pack(side="left", pady=0)



    def _build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        self._build_upload_card(left)
        self._build_documents_card(left)

    def _build_upload_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=PALETTE["card"],
                            corner_radius=12, border_width=1,
                            border_color=PALETTE["border"])
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.columnconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=16, pady=(14, 8))

        ctk.CTkLabel(header_frame, text="📁  Upload Documents",
                     font=self.font_subtitle, text_color=PALETTE["text"]).pack(side="left")

        self.file_count_badge = ctk.CTkLabel(
            header_frame,
            text="0 / 10",
            font=self.font_badge,
            text_color=PALETTE["bg"],
            fg_color=PALETTE["accent"],
            corner_radius=8,
            width=52,
            height=20,
        )
        self.file_count_badge.pack(side="right")

        self.btn_select = ctk.CTkButton(
            card, text="+ Select Files",
            font=self.font_body,
            width=130,
            fg_color=PALETTE["surface"],
            hover_color=PALETTE["border"],
            border_color=PALETTE["border"],
            border_width=1,
            text_color=PALETTE["text"],
            command=self._select_files,
        )
        self.btn_select.grid(row=1, column=0, padx=(16, 8), pady=(0, 14))

        self.selected_label = ctk.CTkLabel(
            card,
            text="No files selected",
            font=self.font_small,
            text_color=PALETTE["muted"],
            anchor="w",
        )
        self.selected_label.grid(row=1, column=1, sticky="w", padx=4)

        self.btn_upload = ctk.CTkButton(
            card, text="Upload ↑",
            font=self.font_body,
            width=120,
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            text_color="#ffffff",
            text_color_disabled="#ffffff",
            state="disabled",
            command=self._upload_files,
        )
        self.btn_upload.grid(row=1, column=2, padx=(8, 16), pady=(0, 14))

    def _build_documents_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=PALETTE["card"],
                            corner_radius=12, border_width=1,
                            border_color=PALETTE["border"])
        card.grid(row=1, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        hf = ctk.CTkFrame(card, fg_color="transparent")
        hf.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))

        ctk.CTkLabel(hf, text="📄  Documents",
                     font=self.font_subtitle, text_color=PALETTE["text"]).pack(side="left")

        btn_refresh = ctk.CTkButton(
            hf, text="⟳ Refresh",
            font=self.font_small,
            width=90,
            fg_color="transparent",
            hover_color=PALETTE["border"],
            border_color=PALETTE["border"],
            border_width=1,
            text_color=PALETTE["muted"],
            command=self._refresh_documents,
        )
        btn_refresh.pack(side="right")

        self._build_doc_table(card)

    def _build_doc_table(self, parent):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        header_row = ctk.CTkFrame(container, fg_color=PALETTE["surface"],
                                  corner_radius=6, height=32)
        header_row.grid(row=0, column=0, sticky="ew")
        header_row.grid_propagate(False)
        header_row.columnconfigure(1, weight=1)

        for col, (label, w) in enumerate([("ID", 50), ("Filename", 0), ("Status", 100), ("Size", 80), ("Action", 60)]):
            ctk.CTkLabel(
                header_row, text=label,
                font=self.font_badge,
                text_color=PALETTE["muted"],
                width=w if w else 0,
                anchor="w",
            ).grid(row=0, column=col, padx=(12 if col == 0 else 4, 4), pady=0, sticky="w")


        self.doc_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=PALETTE["surface"],
            corner_radius=6,
            scrollbar_button_color=PALETTE["border"],
            scrollbar_button_hover_color=PALETTE["accent"],
        )
        self.doc_frame.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        self.doc_frame.columnconfigure(1, weight=1)

        self.doc_rows: list[dict] = []

    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self._build_query_card(right)

    def _build_query_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=PALETTE["card"],
                            corner_radius=12, border_width=1,
                            border_color=PALETTE["border"])
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(4, weight=1)

        ctk.CTkLabel(card, text="🤖  Ask the AI",
                     font=self.font_subtitle, text_color=PALETTE["text"]).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.query_input = ctk.CTkTextbox(
            card,
            height=90,
            font=self.font_body,
            fg_color=PALETTE["surface"],
            border_color=PALETTE["border"],
            border_width=1,
            text_color=PALETTE["text"],
            wrap="word",
            corner_radius=8,
        )
        self.query_input.grid(row=1, column=0, sticky="ew", padx=16)
        self.query_input.insert("0.0", "Ask a question about your documents...")
        self.query_input.bind("<FocusIn>", self._on_query_focus_in)
        self.query_input.bind("<FocusOut>", self._on_query_focus_out)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="e", padx=16, pady=8)

        ctk.CTkLabel(btn_frame, text="Top-K:", font=self.font_small,
                     text_color=PALETTE["muted"]).pack(side="left", padx=(0, 4))

        self.topk_var = ctk.StringVar(value="5")
        topk_entry = ctk.CTkEntry(
            btn_frame, textvariable=self.topk_var,
            width=48, font=self.font_body,
            fg_color=PALETTE["surface"],
            border_color=PALETTE["border"],
            text_color=PALETTE["text"],
        )
        topk_entry.pack(side="left", padx=(0, 12))

        self.btn_send = ctk.CTkButton(
            btn_frame, text="Send →",
            font=self.font_body,
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            text_color="#ffffff",
            text_color_disabled="#ffffff",


            width=100,
            command=self._send_query,
        )
        self.btn_send.pack(side="left")

        ctk.CTkLabel(card, text="Response",
                     font=self.font_small, text_color=PALETTE["muted"]).grid(
            row=3, column=0, sticky="w", padx=16, pady=(6, 2))

        self.answer_box = ctk.CTkTextbox(
            card,
            font=self.font_body,
            fg_color=PALETTE["surface"],
            border_color=PALETTE["border"],
            border_width=1,
            text_color=PALETTE["text"],
            wrap="word",
            corner_radius=8,
            state="disabled",
        )
        self.answer_box.grid(row=4, column=0, sticky="nsew", padx=16)

        ctk.CTkLabel(card, text="References",
                     font=self.font_small, text_color=PALETTE["muted"]).grid(
            row=5, column=0, sticky="w", padx=16, pady=(8, 2))

        self.refs_frame = ctk.CTkScrollableFrame(
            card,
            fg_color=PALETTE["surface"],
            corner_radius=8,
            height=130,
            scrollbar_button_color=PALETTE["border"],
            scrollbar_button_hover_color=PALETTE["accent"],
        )
        self.refs_frame.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.refs_frame.columnconfigure(0, weight=1)

    def _on_query_focus_in(self, event):
        if self.query_input.get("0.0", "end-1c") == "Ask a question about your documents...":
            self.query_input.delete("0.0", "end")

    def _on_query_focus_out(self, event):
        if not self.query_input.get("0.0", "end-1c").strip():
            self.query_input.insert("0.0", "Ask a question about your documents...")

    def _select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[("Supported files", "*.txt *.md *.pdf"), ("All files", "*.*")],
        )
        if not paths:
            return

        available = MAX_FILES - len(self._local_files)
        added = 0
        for p in paths:
            if added >= available:
                break
            pp = pathlib.Path(p)
            if pp in self._local_files:
                continue
            self._local_files.append(pp)
            added += 1

        if len(paths) > added and available > 0:
            messagebox.showinfo("Limit", f"Only first {MAX_FILES} files can be queued.")

        self._update_upload_card()

    def _update_upload_card(self):
        n = len(self._local_files)
        self.file_count_badge.configure(text=f"{n} / {MAX_FILES}")
        if n:
            names = ", ".join(p.name for p in self._local_files[:3])
            if n > 3:
                names += f" +{n - 3} more"
            self.selected_label.configure(text=names, text_color=PALETTE["text"])
            self.btn_upload.configure(state="normal" if not self._upload_in_progress else "disabled")
        else:
            self.selected_label.configure(text="No files selected", text_color=PALETTE["muted"])
            self.btn_upload.configure(state="disabled")

    def _upload_files(self):
        if not self._local_files or self._upload_in_progress:
            return
        self._upload_in_progress = True
        self.btn_upload.configure(state="disabled", text="Uploading…")
        files = list(self._local_files)

        def do_upload():
            try:
                with httpx.Client(timeout=120.0) as client:
                    file_tuples = [
                        ("files", (p.name, p.read_bytes(), "application/octet-stream"))
                        for p in files
                    ]
                    resp = client.post(f"{API_BASE}/upload", files=file_tuples)
                    resp.raise_for_status()
                self.after(0, lambda: self._on_upload_success(files))
            except Exception as exc:
                self.after(0, lambda: self._on_upload_error(str(exc)))

        threading.Thread(target=do_upload, daemon=True).start()

    def _on_upload_success(self, files):
        for f in files:
            if f in self._local_files:
                self._local_files.remove(f)
        self._upload_in_progress = False
        self.btn_upload.configure(text="Upload ↑")
        self._update_upload_card()
        self._refresh_documents()
        messagebox.showinfo("Success", "Files uploaded. Processing has started.")

    def _on_upload_error(self, msg):
        self._upload_in_progress = False
        self.btn_upload.configure(text="Upload ↑")
        self._update_upload_card()
        messagebox.showerror("Upload Error", msg)

    def _refresh_documents(self):
        threading.Thread(target=self._fetch_documents, daemon=True).start()

    def _fetch_documents(self):
        try:
            resp = httpx.get(f"{API_BASE}/documents", timeout=30.0)
            resp.raise_for_status()
            docs = resp.json()
            self.after(0, lambda: self._render_documents(docs))
            self.after(0, lambda: self._set_api_status(connected=True))
        except Exception:
            self.after(0, lambda: self._set_api_status(connected=False))

    def _render_documents(self, docs: list[dict]):
        for widget in self.doc_frame.winfo_children():
            widget.destroy()
        self.doc_rows.clear()
        self._remote_docs = docs

        if not docs:
            ctk.CTkLabel(
                self.doc_frame,
                text="No documents yet. Upload your first file!",
                font=self.font_small,
                text_color=PALETTE["muted"],
            ).grid(row=0, column=0, columnspan=4, pady=24, padx=12)
            return

        for i, doc in enumerate(docs):
            row_bg = PALETTE["card"] if i % 2 == 0 else PALETTE["surface"]
            row_frame = ctk.CTkFrame(self.doc_frame, fg_color=row_bg, corner_radius=4, height=36)
            row_frame.grid(row=i, column=0, sticky="ew", pady=1)
            row_frame.grid_propagate(False)
            row_frame.columnconfigure(1, weight=1)

            ctk.CTkLabel(row_frame, text=str(doc.get("id", "")),
                         font=self.font_small, text_color=PALETTE["muted"],
                         width=50, anchor="w").grid(row=0, column=0, padx=(12, 4), pady=0, sticky="w")

            name = doc.get("filename", "")
            if len(name) > 35:
                name = name[:32] + "..."
            ctk.CTkLabel(row_frame, text=name, font=self.font_small,
                         text_color=PALETTE["text"], anchor="w").grid(
                row=0, column=1, padx=4, sticky="w")

            status = doc.get("status", "")
            color = STATUS_COLORS.get(status, PALETTE["muted"])
            status_badge = ctk.CTkLabel(
                row_frame,
                text=f"● {status}",
                font=self.font_badge,
                text_color=color,
                width=100,
                anchor="w",
            )
            status_badge.grid(row=0, column=2, padx=4, sticky="w")

            size_bytes = doc.get("size", 0) or 0
            size_label = _format_size(size_bytes)
            ctk.CTkLabel(row_frame, text=size_label, font=self.font_small,
                         text_color=PALETTE["muted"], width=80, anchor="e").grid(
                row=0, column=3, padx=4, sticky="e")

            btn_del = ctk.CTkButton(
                row_frame, text="🗑", font=self.font_small, width=30, height=24,
                fg_color="transparent", hover_color=PALETTE["error"],
                text_color=PALETTE["error"],
                command=lambda d=doc: self._delete_document(d["id"]))
            btn_del.grid(row=0, column=4, padx=(4, 12), sticky="e")


        self.doc_frame.columnconfigure(0, weight=1)

    def _delete_document(self, doc_id: int):
        if not messagebox.askyesno("Confirm", f"Delete document #{doc_id}?"):
            return
        
        def do_delete():
            try:
                resp = httpx.delete(f"{API_BASE}/documents/{doc_id}", timeout=30.0)
                resp.raise_for_status()
                self.after(0, self._refresh_documents)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=do_delete, daemon=True).start()


    def _set_api_status(self, connected: bool):
        if connected:
            self.api_status_label.configure(text="API Connected", text_color=PALETTE["success"])
            self.status_dot.configure(fg_color=PALETTE["success"])
        else:
            self.api_status_label.configure(text="API Offline", text_color=PALETTE["error"])
            self.status_dot.configure(fg_color=PALETTE["error"])

    def _send_query(self):
        if self._query_in_progress:
            logger.warning("Query already in progress, ignoring")
            return
        question = self.query_input.get("0.0", "end-1c").strip()
        if not question or question == "Ask a question about your documents...":
            messagebox.showwarning("Empty Query", "Please type a question first.")
            return

        try:
            top_k = int(self.topk_var.get())
        except ValueError:
            top_k = DEFAULT_TOP_K

        logger.info(f"Starting query: '{question[:50]}...' with top_k={top_k}")
        self._query_in_progress = True
        self.btn_send.configure(state="disabled", text="Thinking…")
        self._set_answer("")

        for widget in self.refs_frame.winfo_children():
            widget.destroy()

        def do_query():
            try:
                logger.info("Sending HTTP POST to /api/query...")
                resp = httpx.post(
                    f"{API_BASE}/query",
                    json={"q": question, "k": top_k},
                    timeout=300.0,
                )
                logger.info(f"Received response with status code: {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"Query successful, answer length: {len(data.get('answer', ''))}")
                self.after(0, lambda: self._on_query_success(data))
            except Exception as exc:
                logger.error(f"Query error: {exc}", exc_info=True)
                self.after(0, lambda: self._on_query_error(str(exc)))

        threading.Thread(target=do_query, daemon=True).start()

    def _on_query_success(self, data: dict):
        logger.info("Query success callback triggered")
        self._query_in_progress = False
        self.btn_send.configure(state="normal", text="Send →")
        answer = data.get("answer", "")
        logger.info(f"Setting answer in UI: {answer[:100]}...")
        self._set_answer(answer)
        self._render_refs(data.get("refs", []))

    def _on_query_error(self, msg: str):
        logger.error(f"Query error callback triggered: {msg}")
        self._query_in_progress = False
        self.btn_send.configure(state="normal", text="Send →")
        self._set_answer(f"⚠ Error: {msg}")

    def _set_answer(self, text: str):
        self.answer_box.configure(state="normal")
        self.answer_box.delete("0.0", "end")
        
        self.answer_box._textbox.tag_config("bold", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.answer_box._textbox.tag_config("h1", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), spacing3=6)
        self.answer_box._textbox.tag_config("h2", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), spacing3=4)
        
        lines = text.split("\n")
        for line in lines:
            if line.startswith("# "):
                self.answer_box.insert("end", line[2:] + "\n", "h1")
            elif line.startswith("## "):
                self.answer_box.insert("end", line[3:] + "\n", "h2")
            elif "**" in line:
                parts = line.split("**")
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        self.answer_box.insert("end", part, "bold")
                    else:
                        self.answer_box.insert("end", part)
                self.answer_box.insert("end", "\n")
            else:
                self.answer_box.insert("end", line + "\n")

        self.answer_box.configure(state="disabled")

    def _render_refs(self, refs: list[dict]):
        for widget in self.refs_frame.winfo_children():
            widget.destroy()

        if not refs:
            ctk.CTkLabel(self.refs_frame, text="No references.", font=self.font_small,
                         text_color=PALETTE["muted"]).grid(row=0, column=0, padx=8, pady=8)
            return

        for i, ref in enumerate(refs):
            frame = ctk.CTkFrame(
                self.refs_frame,
                fg_color=PALETTE["card"],
                corner_radius=6,
                border_width=1,
                border_color=PALETTE["border"],
            )
            frame.grid(row=i, column=0, sticky="ew", pady=3)
            frame.columnconfigure(0, weight=1)

            score = ref.get("score", 0)
            filename = ref.get("filename", "?")
            chunk_idx = ref.get("chunkIndex", "?")
            text_snippet = (ref.get("text") or "")[:200]
            if len(ref.get("text", "")) > 200:
                text_snippet += "…"

            meta_frame = ctk.CTkFrame(frame, fg_color="transparent")
            meta_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 0))

            ctk.CTkLabel(
                meta_frame,
                text=f"📄 {filename}  ·  Chunk {chunk_idx}",
                font=self.font_badge,
                text_color=PALETTE["accent"],
            ).pack(side="left")

            ctk.CTkLabel(
                meta_frame,
                text=f"Score: {score:.4f}",
                font=self.font_badge,
                text_color=PALETTE["success"],
            ).pack(side="right")

            ctk.CTkLabel(
                frame,
                text=text_snippet,
                font=self.font_small,
                text_color=PALETTE["muted"],
                wraplength=380,
                anchor="w",
                justify="left",
            ).grid(row=1, column=0, sticky="w", padx=10, pady=(2, 8))

        self.refs_frame.columnconfigure(0, weight=1)

    def _start_refresh_loop(self):
        self._fetch_documents()
        self.after(30000, self._auto_refresh)

    def _auto_refresh(self):
        self._fetch_documents()
        self.after(30000, self._auto_refresh)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


if __name__ == "__main__":
    app = RagApp()
    app.mainloop()
