import fitz
from fastapi import HTTPException, status


class DocProcessing:
    def __init__(self, file_path: str, file_content: bytes):
        self.file_path = file_path
        self.file_content = file_content

    def text_formatter(self, file_str: str) -> str:
        formatted_text = file_str.replace("\n", " ").strip()
        return formatted_text

    def process_doc(self) -> str:
        if self.file_path.endswith(".txt"):
            try:
                file_str = self.file_content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
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
        return self.text_formatter(file_str)
