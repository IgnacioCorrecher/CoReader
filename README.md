# CoReader
RAG Coplitot for reading purposes. Get answers of what you've read without risking an spoiler.

## Backend Setup

1.  **Create a Conda environment:**
    ```bash
    conda create -n coreader-env python=3.12
    ```
2.  **Activate the environment:**
    ```bash
    conda activate coreader-env
    ```
3.  **Install dependencies (assuming you have a requirements.txt file in the backend folder):**
    Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
    Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Frontend Setup

1.  **Navigate to the `frontend` directory (or create it if it doesn't exist):**
    ```bash
    cd frontend
    ```
2.  **Create a new Vite project (if you haven't already):**
    Follow the prompts to select React and TypeScript.
    ```bash
    npm create vite@latest
    ```
    When prompted for the project name, you can use something like `coreader`. This will create a new directory with the project name.
3.  **Navigate into your new project directory:**
    ```bash
    cd your-project-name 
    ```
4.  **Install dependencies:**
    ```bash
    npm install
    ```
5.  **Start the development server:**
    ```bash
    npm run dev
    ```
