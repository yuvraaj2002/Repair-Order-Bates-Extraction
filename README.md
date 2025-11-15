
# Legal Repair Order Bates Number Indexing Tool

## What is this?

This project helps us find and organize **repair order numbers** from lots of legal PDF documents. Each PDF page has a special serial number called a  **Bates number** . We need to match each Bates number to the repair order numbers found in that page.

## Why do we need it?

When working on legal cases, it’s important to know:

* Which repair order shows up on which document/page.
* Which Bates number belongs to each repair order.
* Where to find information fast, so we can answer questions in court or write reports.

## What does it do?

1. **Extracts Numbers:**

   Finds every repair order number (usually 5 digits, sometimes with prefixes like "FOW" or with dashes) in each PDF page.
2. **Links to Bates:**

   Matches every repair order found to the Bates number of that PDF page.
3. **Makes a Table:**

   Saves everything in a simple table. For each page, the table shows:

   * Bates number
   * Page number
   * All the repair order numbers found there
4. **Lets You Search:**

   If you type in a repair order number, you can quickly see all Bates numbers (pages) where it’s found. You get this list as comma-separated numbers so you can copy and paste easily.
5. **Shows Problems:**

   If the tool has trouble finding a clean 5-digit number, it marks that as a possible problem so you can check it manually.

## How does it help?

* Makes it super easy to track and find up to thousands of documents.
* Quickly answers: “Where is this repair order in my documents?”
* Saves lots of time compared to searching one page at a time.
* Helps us avoid mistakes by showing possible errors.

## What do you need to do?

* Give the tool all your Bates-stamped PDF documents
* The tool will run and make a CSV, Excel, or Google Sheet table
* Get results for searching, copying, and reporting

## Who will use it?

* Legal teams needing fast answers for court or reports
* Anyone handling lots of repair order PDF documents

## Extra Information

* The tool can show a percentage for how many repair orders were found correctly.
* Any problems are listed by Bates number so you can fix them.
* The project is flexible for Excel, Google Sheets, or Python script outputs.
