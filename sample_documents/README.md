# 📄 Sample Health Insurance Documents

This folder contains **realistic sample health insurance documents** that you can use to test and demonstrate the Insurance Claims Processing System.

## 📁 Available Documents

### 1. **Health_Insurance_Policy.pdf**
- **Type**: Policy Document
- **Policy Number**: POL-2024-MH-789456
- **Policy Holder**: Rajesh Kumar Sharma
- **Sum Assured**: ₹5,00,000
- **Coverage**: Hospitalization, Pre/Post hospitalization, Ambulance, Day care procedures

### 2. **Health_Insurance_Claim_Form.pdf**
- **Type**: Claim Form
- **Claim Number**: CLM-2024-00567
- **Claim Amount**: ₹1,25,000
- **Hospital**: Apollo Hospital, Mumbai
- **Diagnosis**: Acute Appendicitis
- **Treatment**: Appendectomy (Laparoscopic)

### 3. **Hospital_Bill.pdf**
- **Type**: Hospital Bill
- **Bill Number**: APL-MUM-2024-5678
- **Hospital**: Apollo Hospital, Mumbai
- **Patient**: Rajesh Kumar Sharma
- **Total Amount**: ₹1,25,000
- **Detailed breakdown** of all charges (room, surgery, medicines, tests, etc.)

### 4. **Discharge_Summary.pdf**
- **Type**: Discharge Summary
- **Hospital**: Apollo Hospital, Mumbai
- **Diagnosis**: Acute Appendicitis with peritonitis
- **Procedure**: Laparoscopic Appendectomy
- **Doctor**: Dr. Amit Patel (General Surgeon)
- **Medications** and **follow-up advice** included

---

## 🎯 How to Use These Documents

### **Step 1: Upload Documents**
1. Go to http://localhost:8000
2. Click the **Upload** tab
3. Drag & drop or browse for these PDF files
4. Select appropriate document type:
   - `Health_Insurance_Policy.pdf` → **Policy Document**
   - `Health_Insurance_Claim_Form.pdf` → **Claim Form**
   - `Hospital_Bill.pdf` → **Hospital Bill**
   - `Discharge_Summary.pdf` → **Discharge Summary**
5. Wait 30-60 seconds for processing

### **Step 2: Ask Questions**
Once documents are processed, go to the **Chat** tab and try these questions:

#### **About Policy:**
- "What is the policy number?"
- "What is the sum assured?"
- "What is the coverage amount?"
- "When does the policy expire?"
- "What are the exclusions?"

#### **About Claim:**
- "What is the claim amount?"
- "What hospital was the treatment at?"
- "What was the diagnosis?"
- "When was the patient admitted?"
- "What treatment was performed?"

#### **About Hospital Bill:**
- "What was the total bill amount?"
- "What were the surgery charges?"
- "How many days was the patient hospitalized?"
- "What was the room rent per day?"
- "Was there any discount applied?"

#### **About Discharge:**
- "What medications were prescribed?"
- "What is the follow-up advice?"
- "Who was the treating doctor?"
- "What was the condition at discharge?"

#### **Cross-Document Questions:**
- "Summarize all the key information"
- "Is the claim amount within the policy coverage?"
- "What documents are available?"
- "Compare the bill amount with the claim amount"

---

## 🔄 Regenerate Documents

If you want to create new sample documents with different data:

```bash
cd sample_documents
python create_samples.py
```

This will regenerate all 4 PDF documents in the `output/` folder.

---

## 📊 Document Details

All documents contain realistic information including:
- ✅ Policy numbers, claim numbers, bill numbers
- ✅ Patient demographics (name, age, gender)
- ✅ Medical information (diagnosis, treatment, medications)
- ✅ Financial details (amounts, breakdowns, payments)
- ✅ Dates and timelines
- ✅ Hospital and doctor information
- ✅ Professional formatting and layout

---

## 🎨 Document Features

These sample documents demonstrate:
- **OCR Capability**: Clean, readable text for accurate extraction
- **Entity Extraction**: Multiple entities (amounts, dates, names, policy numbers)
- **Semantic Search**: Related information across multiple documents
- **RAG Chatbot**: Contextual question answering

---

## 📝 Note

These are **fictional documents** created for **demonstration purposes only**. 
All names, numbers, and details are completely made up and do not represent any real person or organization.

---

**Ready to test your Insurance Claims Processing System!** 🚀
