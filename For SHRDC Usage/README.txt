Documentation by William Kee — 12/10/2025
For SHRDC: Operating ERPNext and Automation

This folder contains several Python programs you can run for ERPNext automation.
The workflow is not perfect; feel free to improve and contribute.

Before running, configure the API Key and API Secret, then run Test_bom.py:
- This ensures it can detect BOMs and items and pull the job card properly.
- After successful detection with Test_bom.py, run Automation_WO_Integration.py.
- Complex production chains may sometimes break the cycle; do not expect everything to be perfect.

Example automation process for Automation_WO_Integration.py:
The script detects a submitted Sales Order and ends with a Stock Entry to the Finished Goods warehouse.
Full process:
Sales Order Submit -> Work Order Create and Submit -> Stock Entry of Raw Material to WIP Warehouse ->
Job Card Created and Submitted -> Start Job Card -> Finish Job Card and Submit ->
Final Stock Entry from WIP Warehouse to Finished Product Warehouse

3D printer automation:
This process is similar, but instead of automatically finishing the Job Card, the script will poll the 3D printers for status updates every few seconds.

Process:
Start Job Card -> send API to 3D printer -> 3D printer queues/starts printing -> script polls status ->
Once printing is complete, it marks the Job Card as complete -> Finish Job Card and Submit -> rest of the automation

Before you run, check your connection:
- Are you on the same Wi‑Fi network as the 3D printers/Node‑RED? If not, connect to the same network.
- Use the correct OctoPrint URL.
- Get the API Key and API Secret from your ERPNext server.
- Get the API Key from OctoPrint.
- Run Test_octoprint.py first to establish a connection before running the main automation script.
- Configure OctoPrint properly, then run the main automation program.

To run the 3D printer automation:
python Automation_3DPrinter_ERPNext.py

If the automation runs successfully, you can continue improving and maintaining it. Good luck Have fun!