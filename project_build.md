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

## Chat Interface

### Thinking
We should hae a standard chat interface with a 'thinking' agent
* this 'thinking' agent should be a fast to respond agent and is already implemented in the backend
* it should repeat the user's question then stream back text about how it is considering the problem, is working on the problem.  Basically just show the user something while the Google Sheets API is working

### Right Side Pane for Explainability
The python server is logging great information about the Agent Activity, I would like to expose that to the user.
Can you put an item in the top Navigation next to the help icon, something that is debug related.
If we are on the Agent screen, it should be illuminated and clickable
If clicked it should slide a Pane out from the right and emit all the server logs from the python service and the UI to this pane.

something like
SERVER: Financial agent initialized successfully!
SERVER: [Model Doc Reader] Reading model documentation...
SERVER: INFO:     127.0.0.1:64930 - "GET / HTTP/1.1" 200 OK
SERVER: [Model Doc Reader] Read 2217 characters of documentation.
SERVER: /Users/dereky/old/personal/code/ai-makerspace-code/financial-planner-repo/backend/.venv/lib/python3.11/site-packages/pydantic/main.py:464: UserWarning: Pydantic serializer warnings:
  PydanticSerializationUnexpectedValue(Expected `none` - serialized value may not be as expected [field_name='parsed', input_value=RouterOutput(next='recall...by the 'recall' agent."), input_type=RouterOutput])
  return self.__pydantic_serializer__.to_python(
SERVER: [Supervisor] Routing to: recall
  Reason: The user is asking for information about a specific metric, 'sales for 2024'. This falls under the category of questions about model facts and results, which is best handled by the 'recall' agent.
SERVER: [Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Model Doc Reader] Reading model documentation...
[Model Doc Reader] Read 2217 characters of documentation.
[Recall Agent] Generated response.
[Recall Agent] Processing request...
/Users/dereky/old/personal/code/ai-makerspace-code/financial-planner-repo/backend/.venv/lib/python3.11/site-packages/pydantic/main.py:464: UserWarning: Pydantic serializer warnings:
  PydanticSerializationUnexpectedValue(Expected `none` - serialized value may not be as expected [field_name='parsed', input_value=RouterOutput(next='recall...rics and their values."), input_type=RouterOutput])
  return self.__pydantic_serializer__.to_python(
[Supervisor] Routing to: recall
  Reason: The user is asking for a specific metric, 'revenue for January', which falls under the category of understanding model facts and metrics. The 'recall' agent is best suited to provide information about specific metrics and their values.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.
[Recall Agent] Processing request...
[Recall Agent] Generated response.

UI: rendering bla bla bla



### Previous chats
Theree should be a "chats" feature in the left navigation
use the pattern and UI used by Claude here -> https://claude.ai/recents
chats can be stored in session memory, and dont need more persistance than that.

## Interfacing with the model
In the Agent pane we should have a plus sign to the left of the chat bar that has additional capabilities
you can look here for the design and functionality
https://claude.ai/
when hitting the '+' we want the hover menu to contain 2 options

{ICON} Add New Model
* if this is selected give the user a small text box labeled 'model url:' store this URL in local cache for future usages.
* it should show up in "Load Existing Model" dialog for this session

{ICON} Load Existing Model
* here list the models
  * always default to 'default model'  name: Powdered Drink City  url: https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM
  * list any models that were added using "Load Existing Model"

Do not implement any other features of the claude + sign

the selected model should show as a small chip to the left of the '+' sign icon



## Testing
make sure to write unit tests for all backend components.


