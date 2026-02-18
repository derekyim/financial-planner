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
Output - an output of the business that we are monitoring for heath
Gross Sales, Cash, EBITDA..
The Agent architecture should be
Main Planner agent to determine what task the user wants to do
Sub agents for each Task, there should be 7.  Each Task will have a ‘playbook’ that determines exactly how to accomplish the task.  We will only build out a FEW of these to start 
Strategic Guidance - A RAG application that satisfied rag_requirements.md
Current Trends - a RAG application that uses tavily to search the web for financial news for the past month in Financial Planning and Analysis as well as Wholesale, Retail, Amazon ecommerce, shopify and Tiktok Shop.
Information Recall - An agent that can read the facts of a model
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
My application needs to do RAG (Retrieval Augmented Generation) and AI Evals using the RAGAS framework. Can you follow the same guildelines and technology used in @10_Evaluating_RAG_With_Ragas/Evaluating_RAG_Assignment.ipynb , ie the same embedding model and Vector store and add a sub-agent for "Strategic Guidance" that 1. performs RAG and ALSO add the RAGAS framework to both a) do RAG Evals and b) do Agentic evals for tool calls, etc using @10_Evaluating_RAG_With_Ragas/Evaluating_Agents_Assignment.ipynb.  for RAG please use the approach in 'rag_requirements.md'


Write integration tests for all functions that touch an external resource like a web api, external model or tool.
Write unit tests for all functions for all resoruces that do not touch an external resource, MOCK the responses from the particular tool as appropriate.
Make a /tests directory for unit tests
Make a /integration_tests for all integration tests.



# Example of Financial Model for 2 months
ca		End of Period					20-Jan	20-Feb
		Period Type					Actual	Actual
‚Ä¢		No Errors						
								
	Operational Schedule							
								
	 							
		TODO: add inventory with lead time, to make cash problem harder						
		Revenue Drivers						
		This section summarizes the main drivers for gross sales and other direct costs of revenue including discounts, returns, and chargebacks						
								
		Orders summary						
								
Key Driver		Orders					221207	
Key Driver		AoV (Average Order Value)						
Key Driver		AoV (Average Order Value) (Repeat Purchase)						
Key Driver		CaC (Custom Acquisition Cost)						
Key Driver		Orders Per Customer						
Key Driver		Repeat Purchase Rate						
 		Repeat Orders From Past Cohorts						
 		Total Orders						
								
Key Driver	 	% Discounts (average, % of Gross sales)			 	 	-0.15	
Key Driver	 	% Refunds (average, % of Gross sales)			 	 	-0.01	
Key Driver	 	% Shipping Income (average, % of Gross sales)			 	 	0.02	
								
		Calculated Revenue						
		Gross Sales						
		Gross Sales (REPEAT USERS)						
		Gross Sales (NEW)					16682899	
		% growth						
		Discounts					-351447	
		Refunds (P&L)					-633999	
		Shipping income					1039110	
		Net Revenue (P&L, after refunds)					21418816	
								
								
								
		Summary - Profit & Loss						
								
								
Key Result		Gross Sales					21346139	
Key Result		Discounts					-338183	
Key Result		Returns					-628908	
Key Result		Shipping Income					1047090	
Key Result		Net Revenue					21426138	
								
							1	
		Costs of Goods						
		Product Costs					12499607	
		Import Freight Cost					5267	
		Import Duties & Taxes					-	
		Cost of Goods Sold					12504875	
		% of Net Revenue						
								
Key Result		Gross Profit					8921263	
Key Result		% of Net Revenue					0.42	
								
		Selling Expenses						
		Fulfillment Costs					2885150	
		Shipping Expense					109953	
		Merchant Fees					606855	
		Other Variable Costs					-	
		Direct Variable Costs					3601957	
								
Key Result		Contribution Profit					5319306	
Key Result		% of Net Revenue					0.25	
								
		Marketing Expenses						
		Direct Advertising					9620061	
		Other Advertising					126261	
		Other Marketing					41961	
		Total Advertising and Marketing spend					9788283	
								
Key Result		Contribution Profit After Marketing Expenses						
Key Result		% of Net Revenue						
								
								
								
								
 		Operating Expenses					28401	46232
								
								
Key Result		Operating Income (EBIT)					-28401	-46232
 								
								
Key Result		Cash				-	1285003	1228810









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
The "M - Monthly" tab contains most all of the businesses Results and is the tab that rolls up the Income Statement, Balance Sheet and Cash Flow.  Looking at the "Forecast" column here should be used when answering 'what if' questions for future months
A number of schedule tabs like (DTC, Wholesale, Opex, Assets, AMZN, DTC - Acquisition, DTC - OTP, DTC - SUB, AMZN - OTP, AMZN - SUB, and more) work together to produce data that is fed back into M - Monthly as the final financial plan
Tab naming convention 1: DTC -> usually means a Shopify business, AMZN -> Amazon online, Wholesale -> Wholesale or retail sales
Tab naming convention 2: OTP -> one time purchase, SUB -> Subscription,  AnnualSub -> Annual Subscriptions 
If a cell value in one of the "Schedule" tabs contains •, it is a driver and is what should be changed to run forward looking 'scenarios'.  only change values in columns marked as "Forecast", since you can't change "Acutal" numbers in the past
there may be a "Control Panel - Master" tab which indicates where you change many inputs, check cells on the schedues to see if you can change them or if you should use the "control panel"
the tab "Key Drivers and Results" is a READ ONLY tab for the user to see high level metrics, do not change this tab, although you can use it to get a sense for which "Key Drivers" and "Key Results" the user feels are most important
 
=== First Steps ===
When you open a file, consult the "Critical Formulas" area and understand these formulas
If the customer asks you to do something you cannot do, start from M - Monthly, find the appropriate metric they are looking to optimize for and make a PLAN first to read through the formula chain for a single "Forecast" month 
After you have the plan then repeat back to the user your plan and ask for guidance to proceed.




=== RULES ===
When you take an action you MUST write a row to the AuditLog table with the 1)timestamp in YYYY-MM-DD HH:MM:SS 2) who requested the action 3) status of action (success, failure) 4) description of Action 5) Data .  here the Data column should contian a JSON document of the data generated by this action
If the user asks you to "Complete the Next Dysprosium Task" or something similar, you MUST READ from the "Tasks" tab which contains 1)timestamp 2) who requested the action 3) status of action (success, failure, pending) 4) description of Action 5) Data .	Read the Description and Data, ask the user any questions, and complete the action.
If you complete a "Task" then mark the 'Status' column on the Tasks tab as 'success' and add a timestamp.  Also add a row to the AuditLog






=== CRITICAL FORMULAS ===
 
==== EBITDA ====


Location: 'M - Monthly'!Row 194  |  Formula: =Row191 + Row192 + Row193
EBITDA = EBIT + Depreciation + Amortization



