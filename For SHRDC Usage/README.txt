Documentation by William Kee — 12/10/2025
For SHRDC: Operating ERPNext and Automation

This folder contains several Python programs you can run to automate ERPNext workflows.
The workflow is not perfect; feel free to improve and contribute.

Before running, configure the API key and API secret, then run `Test_bom.py`:
- This ensures the script can detect BOMs and items and retrieve the job card correctly.
- After successful detection with `Test_bom.py`, run `Automation_WO_Integration.py`.
- Complex production chains may sometimes break the workflow; do not expect everything to be perfect.

Example automation process for `Automation_WO_Integration.py`:
The script detects a submitted Sales Order and ends with a stock entry to the Finished Goods warehouse.
Full process (example):
Sales Order submit -> Create and submit Work Order -> Stock entry of raw materials to WIP warehouse ->
Job Card created and submitted -> Start Job Card -> Finish Job Card and submit ->
Final stock entry from WIP warehouse to finished product warehouse

3D-printer automation:
This process is similar, but instead of automatically finishing the Job Card, the script polls the 3D printers for status updates every few seconds.

Process (example):
Start Job Card -> send API to 3D printer -> 3D printer queues/starts printing -> script polls status ->
Once printing is complete, the script marks the Job Card as complete, then finishes and submits the Job Card and continues the rest of the automation.

Before you run the script, check your connection:
- Are you on the same Wi‑Fi network as the 3D printers / Node‑RED? If not, connect to the same network.
- Use the correct OctoPrint URL.
- Get the API key and API secret from your ERPNext server.
- Get the API key from OctoPrint.
- Run `Test_octoprint.py` first to verify the connection before running the main automation script.
- Configure OctoPrint properly, then run the main automation program.

To run the 3D-printer automation:
`python Automation_3DPrinter_ERPNext.py`

If the automation runs successfully, you can continue improving and maintaining it. Good luck — have fun!

The "SQL Query for Metabase" file contains a SQL query ready to paste into Metabase.

To use it, navigate to **+ New** in Metabase and follow these steps:
- Select **SQL Query**.
- Paste the SQL query, then click **Run query**.
- If there are errors, fix them; otherwise, choose **Visualization**.
- Customize the visualization to your liking.