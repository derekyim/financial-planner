# Intro
This project has two pieces a react ui under /ui
an agentic backend and api under /backend/

# Requirements
It needs to satisfy all the requirements here in a web application

https://absorbing-toaster-713.notion.site/The-Certification-Challenge-2e7cd547af3d807996d6ea1e0ec931df#2e7cd547af3d80c9b937e9c10ef34be8

Please read this document and make a TODO to acccomplish all 7 tasks

# Proposal
Here is what I propose to build

read backend/docs/final_assignment.md for details of the implementation
read backend/docs/rag_requirements.md  for details on the internal RAG application

Match the requirements and proposed Agent and architectural elements in these to .md docs to the Project requirements.

## UI
There is a react application already, I want to add a left hand navigation to completely cover all 7 tasks in the above Notion document.

Agent - default location when you load the app.  should render a page to show the agent (this is currently the main ui page under /ui). this should be the default landing page.  It will have sub-agents to satisfy the RAG use case as well as the others.
Idea - containing the project idea from the final_assignment.md
Challenge - contains information to satisfy Task 1 from the Notion Document
Solution - 1 -2 paragraphs on the solution as described in final_assignment.md
Architecture - Architecture diagrams per Task 2 of the notion document
Documentation - Should have subsections for
- RAG Application - Detail approach for Task 3 from Notion document for the INTERNAL rag from rag_requirements.md AND tavily search 
- Evals - docs on evals approach - TASK 5 from Notion
- Next Steps - Indicate the next steps, how this application will change for final "Demo Day" implementation. TASK 7 from notion
Evals - should have subsections for
- Dashboard -  here we need to import code fom ../AIE9/10_Evaluating_RAG_With_Ragas/ and make an /evals/ subdirectory under backend and build out an Evals suite.. for this UI element we are going to provide links to Langgraph showing results..  satisfy task 5 by adding an Evals system
- Improvements- Satisfy task 6 by adding space for listin evaluation based improvements

Please make sure to add a 'product tour' capability. for that look at the approach taken here.
We ultimately want to replicate a feature like this  https://amplitude.com/request-a-demo-product-tours or https://www.appcues.com/use-case/onboarding

look here for an existing implementation..
This should live within our react application and highlight specific parts of the application.
 ../../../../../bainbridge/drivepoint-excel-add-in/src/services/TourEngine.ts
Install react-joyride
- Add `react-joyride` dependency (already used in webapp-mui)
- Handle CSS-selector based tooltips for add-in UI elements

## Testing
make sure to write unit tests for all backend components.


