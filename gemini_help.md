# Gemini CLI Help: Mastering Complex Creations

Welcome to the Gemini CLI! This guide is designed to help you provide the most effective prompts, especially for complex software engineering tasks.

Your insight is correct: the single best way to collaborate on a complex project is to provide a **Project Brief** in a Markdown file (`project_brief.md`). This document becomes our shared understanding of the goal.

---

## The Power of a Project Brief

When you write down the project requirements, you clarify your own thinking, and it allows me to:

1.  **Understand the Full Picture:** I can see the entire scope of the project, not just one small piece at a time.
2.  **Ask Targeted Questions:** I can analyze the brief and ask specific, intelligent questions to resolve ambiguities *before* I write any code.
3.  **Formulate a Coherent Plan:** I can propose a complete development plan, including technology stack, file structure, and implementation steps.
4.  **Work More Autonomously:** With a clear brief, I can work for longer stretches without needing to interrupt you for clarification.
5.  **Produce Better Results:** A detailed brief directly leads to a final product that more closely matches your vision.

---

## How to Structure Your Project Brief

Create a file named `project_brief.md` in your project's root directory. Here is a recommended structure. You don't need to use every section, but the more detail you provide, the better.

### 1. Project Title & High-Level Goal
*   **Title:** A clear, concise name for the project.
*   **Goal/Summary:** A one or two-paragraph summary. What are we building? Why are we building it? Who is it for?

### 2. Core Features
Use a checklist or a bulleted list to describe the essential functionalities of the application.
*   **Feature 1:** User authentication (login, logout, register).
*   **Feature 2:** Create, Read, Update, Delete (CRUD) operations for posts.
*   **Feature 3:** Users can comment on posts.

### 3. Technology Stack & Platform
*   **Platform:** Is this a web application, a command-line interface (CLI), a mobile app, a library?
*   **Language(s):** e.g., Python, TypeScript, Go.
*   **Framework(s):** e.g., React, FastAPI, Node.js/Express, Django.
*   **Database:** e.g., PostgreSQL, SQLite, MongoDB.
*   **Styling (for UIs):** e.g., Bootstrap, Tailwind CSS, Material-UI.

*If you are unsure or have no preference, I will propose a modern, standard stack for you.*

### 4. User Experience (UX) & Design
For any application with a user interface.
*   **Look and Feel:** Describe the desired aesthetic (e.g., "modern and minimal," "professional and corporate," "fun and playful").
*   **User Journey:** Describe the key workflows. For example: "A new user visits the homepage, clicks 'Sign Up', fills out the form, and is then redirected to their new dashboard."
*   **Inspiration:** Feel free to link to any websites or applications that you like the look of.

### 5. Data Model
If your application handles data, describe the main entities and their relationships.
*   **User:** `id`, `username`, `email`, `password_hash`
*   **Post:** `id`, `author_id` (links to User), `title`, `content`, `timestamp`
*   **Comment:** `id`, `post_id` (links to Post), `author_id` (links to User), `text`, `timestamp`

### 6. File & Directory Structure
If you have a preference for how the code should be organized, list it here. Otherwise, I will use standard conventions for the chosen framework.
```
/
├── src/
│   ├── api/
│   ├── components/
│   └── pages/
├── public/
├── package.json
└── README.md
```

---

## Example Project Brief

Here is a complete example for a simple To-Do List web application.

````markdown
# Project Brief: Simple To-Do Web App

## 1. High-Level Goal
The goal is to create a simple, single-page web application for managing a personal to-do list. The application should be clean, fast, and easy to use. It will allow a user to add tasks, mark them as complete, and delete them. Data will be saved in the browser's local storage.

## 2. Core Features
- [ ] View the list of to-do items.
- [ ] Add a new to-do item via an input field and a button.
- [ ] Mark a to-do item as "completed" by clicking on it. This should visually strike through the text.
- [ ] Delete a to-do item by clicking a "delete" button next to it.
- [ ] Persist the to-do list in the browser's `localStorage` so the list is not lost on page refresh.

## 3. Technology Stack & Platform
- **Platform:** Web Application
- **Language(s):** JavaScript (or TypeScript, if you prefer)
- **Framework(s):** React. No backend is necessary.
- **Styling:** Bootstrap CSS for a clean, modern look. Use a standard theme.

## 4. User Experience (UX) & Design
- **Look and Feel:** Minimalist and clean. A single-column layout.
- **User Journey:**
    1. The user opens the page and sees their current to-do list and an input field to add a new task.
    2. The user types a task into the input field and clicks "Add Task".
    3. The new task appears at the bottom of the list.
    4. The user clicks on a task text to toggle its completed status.
    5. The user clicks the "X" button next to a task to remove it permanently.

## 5. Data Model
The data will be an array of "to-do" objects stored in `localStorage`. Each object will have the following structure:
- **Todo Item:** `id` (a unique number or string), `text` (the task description), `completed` (a boolean).
````

---

## Our Collaborative Workflow

1.  **You Provide:** You create and save `project_brief.md`.
2.  **You Prompt:** You tell me: `"I have created a project_brief.md. Please read it, ask any clarifying questions, and then propose a plan to implement it."`
3.  **I Analyze:** I will read the file and ask you questions to fill in any missing details.
4.  **We Align:** We'll discuss the plan until you are happy with it.
5.  **I Build:** I will execute the plan, creating files and writing code.
6.  **We Test & Iterate:** I will help you test the application and make changes based on your feedback.

By following this process, we can build amazing things together.
