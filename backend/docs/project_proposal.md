Final Project Proposal

Goal/Background
To use an agent to answer hard business questions from users based on their Financial model based on the https://www.drivepoint.io/ “SmartModel”.

Drivepoint empowers online retailers using Amazon, Shopify who also sell in Wholesale (COSTCO, Target, etc..) by providing a financial model, reporting, a Data Warehouse and tools.  The goal is to increase customer goal achievement, (profitability, growth, fundraising) through better FP&A (Financial Planning and Analysis).
Use Cases/ User Stories


As a user I want to ask an agent complex questions and receive
Information about my current Finances and Scenarios
Advice on how to improve my business, ie where to look
Answers to ‘what-if’ questions about my business, grounded in my numbers 
Back-looking trends
Forward-looking projections

As a user I want to ask an agent to perform
Model roll-forwards
Report buildouts
Data analysis 
Changes to my model

Example topics are:


Cluster
#
Summary
New Product & Channel Launches
43
The largest cluster — customers constantly model new product/SKU launches across Amazon, DTC, Costco, Whole Foods, Sephora, Ulta, Target, Albertsons, HEB, Food Service, and new stores with varying costs, promos, and velocities.
Marketing Spend & CAC Scenarios
29
Heavy interest in adjusting paid media (Google, TikTok, Amazon, blended CAC) and understanding the effect on sales, EBITDA, or retention.
Tariffs & Cost Shocks
17
Many prompts ask about tariff impacts (10%, 15%, 35%) across all or some SKUs, plus knock-on effects on sales and wholesale expansion.
Bundling & Pricing Experiments
9
Users explore new product bundles, discounts, pre-orders, and AOV adjustments to see impact on margin and sales mix.
Subscriptions & Retention
6
Requests to model subscription uptake, repeat purchase increases, retention marketing agencies/software, and LTV improvement.
Wholesale/Retail Expansion & Velocity
14
Prompts about adding doors in Albertsons, Sephora, Costco, Ulta, Target, and boosting velocities with trade spend.
Opex, Payroll & Store Openings/Closings
9
Includes adding payroll costs, hiring reps/brokers, opening/closing retail stores, and brand collab fees.
Cost Structure & Fulfillment
8
Adjustments to shipping, fulfillment, MOQs, warehouse costs, or inbound freight optimizations.
Profitability & Trend Analysis
6
Customers directly ask “do I ever get profitable?”, request margin views vs benchmarks, and trend summaries from actuals.
General Strategy Questions
8
Higher-level asks like “How can I improve my cash conversion cycle?” or “What strategies can I implement to reduce CAC and increase LTV?” plus DTC driver clarifications.


Requirements
The agent should be able to:
List my plans
Answer questions about any of my ‘plans’ current state
Perform what-if analyses
Perform sensitivity analyses
Give suggestions on ‘what do i do next?
Create a new model based on an existing model and save that
Add a new Skill or “schedule” to a model ie “I want to sell in Walmart next year, model that for me”

Technology and Tools Available
All data from the model is available in Bigquery
There is a Tool/API available to get the Formulas, values, tabs from Excel
There is a Tool/API available to make changes in Excel and get new results
There is a Tool/API available to create models from other models and apply changes.
There is the possibility to build a traditional ML Regression model to be able to do predictions.
Challenges / Interesting Facts
The SmartModel is an Excel file that lives in Sharepoint.
It ranges in size from 30-100MB and does NOT fit into context.
It does have tabs by topic ‘Amazon - Subscribers’ that can be known to an agent 
It spans 10+ years of history with almost all tabs having a Monthly date spine across the top and metrics/values/drivers/results in columns A,B,C.


Proposed Architecture and Design
Proposal for new Multi-Agent Architecture
Multi agent router at the front to determine the topic of conversation (use fast, cheap, lightweight model)
Info request
Scenario Planning
DTC (shopify)
AdSpend
Add products/SKUs, Add Wholesales/Retailers
Fundraising Helper
Sensitivity Analysis
Analyze top line metrics, suggest path forward
And many more…
Special “Topic” Planning Agents (10+ medium weight)
Understand concepts
Understand specific Tabs of the model
Can make a plan
Execution Agents (??)
Know how to manipulate formulas in Excel or call tools to make changes
Results Interpretation Agents
Can look at 2 data sets and perform analyses on
What changed
What were impacts
What you could try next
What stats do we need here?
Whats a good way to visualize the change(s)
Text packaging Agents 
Take what was said, format it
Build charts/tables/viz to show
Ask user for next steps

Concrete Proposal
I will provide a Ghseet with basic AdSpend Revenue build for an Ecommerce business “Powedered Drink City”
https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit?gid=1218171431#gid=1218171431
The goal of this project is to be able to perform deep financial analyses of these business using a
Multi-agent system
With multiple memory types
We have these tools
Code in sheets_utilieis.py to use the Gsheets API to Manipulate data
Code in sheets_perform_sensitivities.py to perform sensitivity analyses
The primary workflow for this agent will be
Ask the user
Vocabulary
Key Driver - an Input to the business that can be changed
AdSpend, CaC, Product Price
Key Result - an output of the business that we are monitoring for heath
Gross Sales, Cash, EBITDA..
The Agent architecture should be
Main Planner agent to determine what task the user wants to do
Sub agents for each Task, there should be 5.  Each Task will have a ‘playbook’ that determines exactly how to accomplish the task.  We will only build out a FEW of these to start 
Information Recall - An agent that can read the facts of a model
Market Analysis - 
Forecast Projection - An agent that can look at historical trends of a metric and fill data forward
Sensitivity Analysis - An agent that can perform 1 or 2 variable sensitivities and build sensitivity tables
What If - An agent that can analyze model formulas and answer questions like ‘what would happen to my EBITDA if i raised prices by $5 in 2026?’
Goal Seek - An agent that can dun deep scenarios on questions like ‘I want to get 10% more EBITDA, grow by 10% Gross Sales Year over Year AND never get below 1M in cash, give me the paths to get there”
Goal Seek Playbook 1 - Optimize FOR Cash, Gross Sales Growth and EBITDA
Goal Seek Playbook 2 - Optimize FOR Gross Sales Growth
Goal Seek Playbook 3 - Optimize FOR EBITDA
Each Financial model will contain a tab “Model Documentation” that explains how the model is structured.  The Planner agent should read this FIRST
It should look at all Key Results and build out the formula chain for them
Feature Goal Seek - this is a very complex feature where the “Goal Seek” sub agent will have to try to hit a user’s goals for target variables “Key Results” by altering “Outputs”
Using intuition to determine which Key Drivers have the MOST impact on each of the Key Results
It can work similar to the MS Excel “Solver” function -> https://ocw.mit.edu/courses/15-053-optimization-methods-in-management-science-spring-2013/d906211f43ab4e481dc98e2f160ba1d9_MIT15_053S13_tut03.pdf
A user will provide up to 3 output target with
Metric Name
End Date
Target Value
The Agent should make up test cases that try to satisfy these conditions and produce 3 unique combinations of Key Driver variables that reach the desired Key Result. Latin hypercube sampling is one possible approach to get operating points.
When the Agent is asked to “Understand the Model” it should
Take every Key Result metric and trace the formulas to understand the chain of cells and operations that lead to its calculation.  It should do this in a row that is a “Forecast” period in the future so say ‘June - 25’


Concrete Actions
Build out a series of agents in a new agents.py file that satisfy the above
Use Langchain/LangGraph and LangSmith for the build.
You will have a .env file with all the api keys needed and listed in the final_assignment.ipynb file
Use any approaches in ../05_Multi_Agent_with_LangGraph/Multi_Agent_Applications_assignment.ipynb
Write MOST of your code in library files and use final_assignment.ipynb to be the entry point for easy testing


# Example of Financial Model




ca


End of Period








Jan-20




Period Type








Actual
•


No Errors




























Operational Schedule














































TODO: add inventory with lead time, to make cash problem harder














Revenue Drivers














This section summarizes the main drivers for gross sales and other direct costs of revenue including discounts, returns, and chargebacks






























Orders summary


























Key Driver


Orders








221207.00
Key Driver


AoV (Average Order Value)










Key Driver


AoV (Average Order Value) (Repeat Purchase)










Key Driver


CaC (Custom Acquisition Cost)










Key Driver


Orders Per Customer










Key Driver


Repeat Purchase Rate














Repeat Orders From Past Cohorts














Total Orders


























Key Driver


% Discounts (average, % of Gross sales)








-0.15
Key Driver


% Refunds (average, % of Gross sales)








-0.01
Key Driver


% Shipping Income (average, % of Gross sales)








0.02




















Calculated Revenue














Gross Sales














Gross Sales (REPEAT USERS)














Gross Sales (NEW)








16682899.00




% growth














Discounts








-351447.00




Refunds (P&L)








-633999.00




Shipping income








1039110.00




Net Revenue (P&L, after refunds)








21418816.00




















































Summary - Profit & Loss










































Key Result


Gross Sales








21346139.00
Key Result


Discounts








-338183.00
Key Result


Returns








-628908.00
Key Result


Shipping Income








1047090.00
Key Result


Net Revenue








21426138.00






























1.00




Costs of Goods














Product Costs








12499607.00




Import Freight Cost








5267.00




Import Duties & Taxes








-




Cost of Goods Sold








12504875.00




% of Net Revenue


























Key Result


Gross Profit








8921263.00
Key Result


% of Net Revenue








0.42




















Selling Expenses














Fulfillment Costs








2885150.00




Shipping Expense








109953.00




Merchant Fees








606855.00




Other Variable Costs








-




Direct Variable Costs








3601957.00
















Key Result


Contribution Profit








5319306.00
Key Result


% of Net Revenue








0.25




















Marketing Expenses














Direct Advertising








9620061.00




Other Advertising








126261.00




Other Marketing








41961.00




Total Advertising and Marketing spend








9788283.00
















Key Result


Contribution Profit After Marketing Expenses










Key Result


% of Net Revenue














































































Operating Expenses








28401.00
































Key Result


Operating Income (EBIT)








-28401.00
































Key Result


Cash






-
1285003.00




































The Current “Model Documentation” tab looks like this

=== MODELING CONVENTIONS ===
This is a 3 statement model for historical "Actual" and future "Forecast" periods.  All tabs that contribute to the model share the same formatting detailed below.
Column A contains markers for if something is an Input (contains • )
Column A contains markers for if something is a driver of the business of high importants (marked with "Key Driver" )
Column A contains markers for if something is a result of the business of high importants (marked with "Key Result" )
Coulmn B contains the "durable_ids", a set of ids for each driver or result
Column C contains the "Friendly Name" of a Driver or Metric
Column K is the FIRST column of the date spine, this occurs in cell K2 and continues outward for each month..
Column K months are represented as the fiscal 'last day of the month'
Row 2 contains the date spine
Row 3 contains if this period is an "Actual" or historical value or a "Forecast" value
The "operations" tab contains most all of the businesses Results and is the tab that rolls up the Income Statement, Balance Sheet and Cash Flow.  Looking at the "Forecast" column here should be used when answering 'what if' questions for future months
A number of schedule tabs like (DTC, Wholesale, Opex, Assets, AMZN, DTC - Acquisition, DTC - OTP, DTC - SUB, AMZN - OTP, AMZN - SUB, and more) work together to produce data that is fed back into operations as the final financial plan
Tab naming convention 1: DTC -> usually means a Shopify business, AMZN -> Amazon online, Wholesale -> Wholesale or retail sales
Tab naming convention 2: OTP -> one time purchase, SUB -> Subscription,  AnnualSub -> Annual Subscriptions 
If a cell value in one of the "Schedule" tabs contains •, it is a driver and is what should be changed to run forward looking 'scenarios'.  only change values in columns marked as "Forecast", since you can't change "Acutal" numbers in the past
there may be a "Control Panel - Master" tab which indicates where you change many inputs, check cells on the schedues to see if you can change them or if you should use the "control panel"
the tab "Key Drivers and Results" is a READ ONLY tab for the user to see high level metrics, do not change this tab, although you can use it to get a sense for which "Key Drivers" and "Key Results" the user feels are most important
 
=== First Steps ===
When you open a file, consult the "Critical Formulas" area and understand these formulas
If the customer asks you to do something you cannot do, start from operations, find the appropriate metric they are looking to optimize for and make a PLAN first to read through the formula chain for a single "Forecast" month 
After you have the plan then repeat back to the user your plan and ask for guidance to proceed.




=== RULES ===
When you take an action you MUST write a row to the AuditLog table with the 1)timestamp in YYYY-MM-DD HH:MM:SS 2) who requested the action 3) status of action (success, failure) 4) description of Action 5) Data .  here the Data column should contian a JSON document of the data generated by this action
If the user asks you to "Complete the Next Drivepoint Task" or something similar, you MUST READ from the "Tasks" tab which contains 1)timestamp 2) who requested the action 3) status of action (success, failure, pending) 4) description of Action 5) Data .	Read the Description and Data, ask the user any questions, and complete the action.
If you complete a "Task" then mark the 'Status' column on the Tasks tab as 'success' and add a timestamp.  Also add a row to the AuditLog






=== CRITICAL FORMULAS ===
 
==== EBITDA ====


Location: 'operations'!Row 194  |  Formula: =Row191 + Row192 + Row193
EBITDA = EBIT + Depreciation + Amortization





Feedback - Chris A
10 week project.
It’s mostly possible.
Work on ‘composable AI’
Pick a specific favorite feature.
To learn how to do the rest of them..


We will get ot agent, multi agent, tools, memory
Any of the facets we’ll pick.

Go attend Greg’s office hours..  ‘Project guy’

Maybe start top down..
See if it can page in knowledge

They talk about hierarchical agent, controller at the top.

Multi-agent SDK pick?
Langchain ecosystem
Can talk to openRouter
One api per every model

Fine tune a-priori and then answer questions:
he thinks, in a condensed course setting, the context required to have fine tuning work is really tough
You have to spend a ton of time learning it
It has value

Customization is still a high-leverage thing to do
At some point you’ll end there
And be very happy about it

Opinion.. 
Ai solves zero data problem
Large generalist model can tide me over
Until i can produce an actual specialist
Eventually you have to leverage it

Excel Formulas
Better off to use a tool
Wouldn’t rely on ‘in the head’ calculations
Reasoning traces are not consistent run to run
Compute
Let it run 64 times
Then take the consensus run..  Way slower than 1 shot.
You’re better off doing the calculations
Even if costly and slow




Router agent:
fancy/expensive classifier
Should become a small classifier - that is cheap/fast


Beads - hacky gross context management
Agent and sub agent assembly system ‘gastown’.
For claude workers, and workers

“Ralph’.. Keep poking the agent while it said it wasnt done. Keep poking the agent in a while loop.
“Ralph Wiggum” - programmatically prod Claude

https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum

Github snarktank ralph as well

