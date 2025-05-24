import fitz
from fastapi import HTTPException, status


class DocProcessing:
    def __init__(self, file_path: str, file_content: bytes):
        self.file_path = file_path
        self.file_content = file_content

    def text_formatter(self, file_str: str) -> str:
        # Improve text formatting to preserve natural breaks for better chunking
        import re

        # First, normalize line endings
        formatted_text = file_str.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive whitespace but preserve paragraph structure
        # Replace 3+ consecutive newlines with exactly 2 newlines (paragraph breaks)
        formatted_text = re.sub(r"\n{3,}", "\n\n", formatted_text)

        # Keep double newlines as paragraph separators
        # For single newlines, replace with space only if they're not at the end of sentences
        # This preserves natural sentence and paragraph boundaries
        formatted_text = re.sub(r"(?<![.!?])\n(?![A-Z\n])", " ", formatted_text)

        # Clean up multiple spaces but keep single spaces
        formatted_text = re.sub(r" {2,}", " ", formatted_text)

        # Ensure there are paragraph breaks for better chunking
        # Add paragraph breaks before common chapter/section indicators
        formatted_text = re.sub(
            r"(?<!^)(?=Chapter \d+|CHAPTER \d+|Section \d+|SECTION \d+)",
            "\n\n",
            formatted_text,
        )

        return formatted_text.strip()

    def process_doc(self) -> str:
        if self.file_path.endswith(".txt"):
            try:
                file_str = self.file_content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not decode file contents as UTF-8",
                )
        elif self.file_path.endswith(".pdf"):
            try:
                doc = fitz.open(stream=self.file_content, filetype="pdf")
                file_str = ""
                for page in doc:
                    file_str += page.get_text()
                doc.close()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not process PDF file: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type",
            )
        final_file_str = self.text_formatter(file_str)

        if len(final_file_str) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )

        return final_file_str
