Project Overview  
---

The Peer Evaluation Application is a web-based platform designed to create a method for teachers to post assignments that students can complete and hand in. Once they have been handed in, students can peer review others and teachers can provide feedback. 

The system allows instructors to organize students into groups and define how peer evaluations are conducted using structured criteria. Students are able to review their peers’ work anonymously, providing both scores and written feedback based on the given rubric.

The application collects these evaluations and presents them in a clear and organized manner, allowing instructors to better understand individual contributions within group work. This helps ensure that grading is more fair and reflective of the student’s effort.

The platform supports a more transparent and consistent evaluation process by enabling structured feedback, improving accountability among group members, giving both students and instructors a better insight into performance.

Installation Instructions (Getting Started)   
---

If difficulties arise during the installation process, please refer to the **Troubleshooting** section. 

The following tools must be installed before setting up the development environment: 

| Tool  | Minimum Version | Check Command |
| :---- | :---- | :---- |
| Python | 3.8+ | Python –version |
| Node.js | 20.x LTS | Node –version |
| Npm  | Included with Node | Npm –version |
| Git  | Any recent | Git –version |

OS-Specific Notation:

Windows: Use PowerShell (**not CMD**). You may need to adjust execution policies for Python venv.  
macOS: Use python3 and pip3 commands (not python/pip).  
Linux: Most tools available via package manager (apt, dnf, etc.).

Initial Setup Guide: 

This project uses a Flask backend, backend server, frontend, and frontend server that must be configured. 

1. Use the following link to make a clone of the github repository

	git clone [https://github.com/COSC470Fall2025/Peer-Evaluation-App-V1.git](https://github.com/COSC470Fall2025/Peer-Evaluation-App-V1.git)  
cd Peer-Evaluation-App-V1

2. Set up the Flask Backend   
     
   For Powershell:   
     
   `cd flask_backend`  
   `python -m venv venv`  
   `.\venv\Scripts\Activate.ps1`  
   `pip install -e .`  
   `pip install -r requirements-dev.txt`  
   `$env:FLASK_APP = "api"       # Required for all flask CLI commands in this session`  
   `flask init_db`  
   `flask add_users`  
     
   For MacOS/Linux:   
     
   `cd flask_backend`  
   `python3 -m venv venv`  
   `source venv/bin/activate`  
   `pip install -e .`  
   `pip install -r requirements-dev.txt`  
   `export FLASK_APP=api`  
   `flask init_db`  
   `flask add_users`  
     
3. Begin starting up the backend server   
   

Keep your terminal open with the virtual environment activated, then run:

`Flask run` 

The expected output should be the following: 

 `* Running on http://127.0.0.1:5000`  
 `* Debug mode: on`

This means that the backend server is now running on localhost 5000\. 

4. Perform setup of frontend   
     
   In a new terminal, navigate to the frontend directory:  
     
   `cd frontend`  
   `npm install`  
     
5. Startup the frontend server   
     
   `npm run dev`  
   

The expected output should be the following: 

  `VITE v5.x.x  ready in xxx ms`

  `➜  Local:   http://localhost:3000/`  
  `➜  Network: use --host to expose`

This verifies the frontend is running on port 3000\. 

**Initial setup is now complete\! Here is what we’ve done so far.** 

* Created an isolated Python environment  
* Installed all backend dependencies  
* Created an SQLite database with proper schema  
* Added sample users (student, teacher, admin)  
* Installed all required frontend dependencies (React, Vite, TypeScript, etc.)

Troubleshooting: 

Common Installation Issues 

If Python is not found \- 

* Download from python.org  
* Run installer and check "Add Python to PATH"  
* Restart terminal

 	  
	If [Node.js](http://Node.js) is not found \- 

* Download Node.js 20.x LTS from nodejs.org  
* Run installer (npm comes with it)  
* Restart terminal  
* Verify: node \--version && npm \--version

	  
	

If activation of the virtual environment fails \- 

`# Run as Administrator or use:`  
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

`# Then try activating again:`  
`.\venv\Scripts\Activate.ps1`

   If pip installation fails during setup \-   
	 

* Update pip:

  `python -m pip install --upgrade pip`


* Check Python version:

`python --version  # Must be 3.8+`

* Clear pip cache:

`pip cache purge`  
`pip install -e . --no-cache-dir`

* Install build tools (if compilation errors):

`# macOS:`  
`xcode-select --install`

`# Ubuntu/Debian:`  
`sudo apt install build-essential python3-dev`

`# Windows:`  
`# Install Visual Studio Build Tools from microsoft.com`

Codebase Information: 

This project uses various entry points, controllers, database models, routes and clients to function. These codebases can be explored by referring to the following files within the project. 

* Backend entry point: `flask_backend/api/__init__.py`  
* Backend controllers: `flask_backend/api/controllers/`  
* Database models: `flask_backend/api/models/`  
* Frontend routes: `frontend/src/App.tsx`  
* API client: `frontend/src/util/api.ts`

What Should Be Configured Now: 

At this point, you should have the following setup steps working on your Windows, Max, or Linux machine. 

Backend API running on [http://localhost:5000](http://localhost:5000) (without this, you cannot view the frontend).  
SQLite database filled with sample data (To test login for teachers and students).   
Flask REST API with JWT authentication (for linking the frontend and backend).  
Role-based access control (Students should not have the same access authentication as teachers).   
Frontend SPA running on [http://localhost:3000](http://localhost:3000).  
React \+ TypeScript \+ Vite communicates with the backend via REST API.  
Protected routes with authentication (for privacy and security). 

Congratulations\!

The project has been successfully installed and set up, and can now be worked on. Refer to the codebase information sections on where to begin for implementing any changes. 

Design and Architecture  
---

Architecture Style:  
The project follows a client-server architecture consisting of a React-based frontend and a Flask-based backend. The frontend handles user interface rendering and client side logic, while the backend manages application logic, data processing, and database operations.

Frontend Architecture:  
The frontend is organized around page components that represent the main views of the application. We have pages such as the login, registration and profile pages. Each page is responsible for rendering its specific interface, managing its own state, handling user interactions, and coordinating navigation between different parts of the application. These pages communicate with the backend and perform client side validation before submitting data to the database.

Backend Architecture:  
The backend is structured around controller modules that define API endpoints using Flask blueprints. Each controller is responsible for handling specific functions such as user management, admin operations and assignment-related features. These controllers process incoming HTTP requests, validate input data, enforce authentication and role-based access control, and return the appropriate JSON responses. These controls delegate business logic and database operations to underlying models and services. Security is enforced through authentication, as admin users can determine what permissions each user would have.

Testing Instructions  
---

What Requires Tests:  
All backend code must have tests. Backend code includes:

- New API endpoints  
- New model methods  
- Authentication/authorization logic  
- Data validation  
- Database operations

Frameworks Used and Testing Guidance:

To effectively test the software, we primarily used the pytest framework in order to catch bugs and find discrepancies in the code easier. We utilized this framework as the system implements the Python Programming Language more than any other programming language for functionality.

Test Files Location:

The location for test files are located within the /flask\_backend/tests directory. Keeping the test files together results in a cleaner, more intuitive system model, and allows for easier findings of specific tests.

Writing Good Tests:

The following is a basic test structure to use as guidance in building your own tests for the backend of the system. It is referred to as the ‘AAA pattern’ when writing tests:

`def test_example(test_client):`  
    `# ARRANGE - Set up test data`  
    `user_data = {"email": "test@example.com", "password": "pass123"}`  
      
    `# ACT - Perform the action`  
    `response = test_client.post("/auth/login", json=user_data)`  
      
    `# ASSERT - Verify the outcome`  
    `assert response.status_code == 200`  
    `assert response.json["role"] == "student"`

Feel free to adjust this example code however you see fit when creating your own tests.

Test Naming Conventions:

When naming your specific tests, it is best to follow the guidelines that we used when developing them. For our program, we created descriptive names for the tests such as ‘test\_create\_assignment\_with\_due\_date’ where it clearly states what the test is trying to accomplish. The general naming convention that we used was ‘test\_\<feature\>\_\<scenario\>’ where with our example, ‘create\_assignment’ is the feature, and ‘with\_due\_date’ is the scenario.

Setting up the Testing Environment:

To set up the testing environment, you will need to navigate to the flask\_backend directory of the peer evaluation folder. This can be done by executing:

- `cd flask_backend`

In your system's powershell terminal. After executing this command and seeing that you are in the flask\_backend directory, you can then move on to the **Executing Tests** section of the guide.

Executing Tests:

There are many different types of test executions that you can utilize in the system. These include:

- Running All Backend Tests:  
  * This runs all of the tests which have been created for the system to the current time.  
  * Powershell input:  
    * `source venv/bin/activate  # or .\venv\Scripts\Activate.ps`  
      `# on Windows`

    `pytest`

- Running a Specific Test File:  
  * This runs every test which has been made on a certain, specific file that you give the terminal.  
  * Powershell input:  
    * `pytest tests/<test-file-name>.py`

- Running a Specific Test Function:  
  * This runs only the specified test function in a single testing file.  
  * Powershell input:  
    * `pytest tests/<test-file-name>.py::<test-function-name>`

Along with many different testing options such as:

- Running with Verbose Output:  
  * This runs any of the test executions, with more detailed output and feedback to the user.  
  * Powershell input:  
    * `pytest -v`

- Running with Coverage:  
  * This runs the tests and shows how much of your system is being covered by the specified tests given.  
  * Powershell input:  
    * `pytest --cov=api --cov-report=html`

- Running tests on File Change:  
  * This runs the tests when you change to a different file to see if changing the file of the tests affects the system quality.  
  * Powershell input:  
    * `pip install pytest-watch`  
      `ptw`  
      

With these, you will be able to run any test that you created in the system, as long as the programming language that is being used on the file is in Python.

Coding Standards  
---

Backend:

For the backend of our system, we primarily used Python. For the coding structure, we generally used the PEP 8 style guide, and also used meaningful variable and function names. On top of that, we also added docstrings to functions and classes, and set a maximum line length of 120 characters. We also used type hints to keep our variables, along with the values in them, consistent and more readable, since Python does not have necessary typing.

Frontend:

For the frontend of our system, we primarily used TypeScript. We utilized the types that are provided in TypeScript, and avoided the ‘any’ type as much as possible. We ensured to give each element meaningful names, so buttons weren’t confused for each other. Furthermore, we followed the patterns that previously existed with the components we used, and used hooks with functional components.

Definition of Done:

The point that we would specify a feature as ‘Done’ followed some specific guidelines.  
These guidelines include:

- Code:  
  * Follows our projects coding standards, which are specified in the Frontend and Backend section of Coding Standards.  
  * Does not result in linting errors.  
  * No commented-out code sections, along with debug statements, which may confuse future developers for its existence.  
  * Variables and Functions must have meaningful names.  
  * Comments for explaining complex logic segments.  
- Documentation:  
  * Each endpoint in the API is documented in the ‘ENDPOINT\_SUMMARY.md’ file.  
  * Updated README file if there is a new dependency added to the system.  
  * Features that users will interact with are recorded in the documentation.  
- Functionality:  
  * New features work as described in the User Stories.  
  * The new feature does not introduce any new bugs to the system.  
  * If working with frontend, you should be able to run and test the feature on multiple different browsers such as Chrome, Firefox, etc..  
  * The features should also be able to work on different operating systems such as Mac, Windows, Linux, and others.  
- Review:  
  * At least one other developer/peer must approve of the feature and have it working on their system.  
  * If there is feedback from the reviewer, it is addressed and implemented if the feedback is reasonable and within the scope of the feature.

Once all of these requirements are checked, you may create a pull request in the Github repository which has a clear description and name. After approval from team members, merge this branch into the main system branch, and delete the branch that originally created the feature.

Revision History  
---

| Version | Date | Author(s) | Description of changes |
| :---- | :---- | :---- | :---- |
| 0.1 | 2026-03-16 | Tanner, Josh, Connor, Troy, Liam | Initial outline of developer guide created. Product overview and basic structure. |
| 0.2 | 2026-03-17 | Troy | Added section for Coding Standards |
| 0.5 | 2026-03-17 | Tanner | Added step by step for the installation guide. |
| 0.6 | 2026-03-18 | Gabe | Added instruction set for testing. |
| 0.8 | 2026-03-19 | Connor | Added information for project overview. Added information about project design and architecture |
| 1.0 | 2026-03-19 | Josh, Liam | Final review, proofreading and approval.  Document finalized for submission. |

