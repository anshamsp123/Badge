"""
Generate sample health insurance documents for demo purposes
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime, timedelta
import os

# Create output directory
os.makedirs('output', exist_ok=True)

def create_health_insurance_policy():
    """Create a sample health insurance policy document"""
    filename = 'output/Health_Insurance_Policy.pdf'
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph("HEALTH INSURANCE POLICY", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Company header
    story.append(Paragraph("SecureHealth Insurance Company Ltd.", styles['Normal']))
    story.append(Paragraph("123 Insurance Plaza, Mumbai - 400001", styles['Normal']))
    story.append(Paragraph("Phone: 1800-XXX-XXXX | Email: support@securehealth.com", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Policy details
    story.append(Paragraph("POLICY DETAILS", heading_style))
    
    policy_data = [
        ['Policy Number:', 'POL-2024-MH-789456'],
        ['Policy Holder:', 'Rajesh Kumar Sharma'],
        ['Date of Birth:', '15/03/1985'],
        ['Policy Issue Date:', '01/01/2024'],
        ['Policy Expiry Date:', '31/12/2024'],
        ['Sum Assured:', '₹5,00,000'],
        ['Premium Amount:', '₹15,450 per annum'],
        ['Policy Type:', 'Individual Health Insurance'],
    ]
    
    policy_table = Table(policy_data, colWidths=[2.5*inch, 4*inch])
    policy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(policy_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Coverage details
    story.append(Paragraph("COVERAGE DETAILS", heading_style))
    
    coverage_data = [
        ['Coverage Type', 'Limit'],
        ['Hospitalization Expenses', '₹5,00,000'],
        ['Pre-hospitalization (60 days)', '₹25,000'],
        ['Post-hospitalization (90 days)', '₹25,000'],
        ['Ambulance Charges', '₹2,000 per hospitalization'],
        ['Day Care Procedures', 'Covered'],
        ['Room Rent', '₹3,000 per day (max)'],
    ]
    
    coverage_table = Table(coverage_data, colWidths=[4*inch, 2.5*inch])
    coverage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    story.append(coverage_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Exclusions
    story.append(Paragraph("EXCLUSIONS", heading_style))
    exclusions = """
    1. Pre-existing diseases (covered after 2 years)<br/>
    2. Cosmetic or plastic surgery<br/>
    3. Dental treatment (unless due to accident)<br/>
    4. Maternity expenses<br/>
    5. Treatment outside India<br/>
    6. Self-inflicted injuries<br/>
    """
    story.append(Paragraph(exclusions, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("This is a computer-generated document and does not require signature.", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))
    
    doc.build(story)
    print(f"✓ Created: {filename}")

def create_claim_form():
    """Create a sample health insurance claim form"""
    filename = 'output/Health_Insurance_Claim_Form.pdf'
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#c62828'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("HEALTH INSURANCE CLAIM FORM", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Claim details
    claim_data = [
        ['Claim Number:', 'CLM-2024-00567'],
        ['Policy Number:', 'POL-2024-MH-789456'],
        ['Claim Date:', '15/11/2024'],
        ['Policy Holder:', 'Rajesh Kumar Sharma'],
        ['Patient Name:', 'Rajesh Kumar Sharma'],
        ['Hospital Name:', 'Apollo Hospital, Mumbai'],
        ['Date of Admission:', '10/11/2024'],
        ['Date of Discharge:', '13/11/2024'],
        ['Diagnosis:', 'Acute Appendicitis'],
        ['Treatment:', 'Appendectomy (Laparoscopic)'],
        ['Total Claim Amount:', '₹1,25,000'],
    ]
    
    claim_table = Table(claim_data, colWidths=[2.5*inch, 4*inch])
    claim_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ffebee')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(claim_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Bill breakdown
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#c62828'),
        spaceAfter=12
    )
    
    story.append(Paragraph("BILL BREAKDOWN", heading_style))
    
    bill_data = [
        ['Description', 'Amount (₹)'],
        ['Room Charges (3 days @ ₹2,500/day)', '7,500'],
        ['Surgery Charges', '45,000'],
        ['Surgeon Fees', '25,000'],
        ['Anesthesia Charges', '8,000'],
        ['Medicines and Consumables', '15,500'],
        ['Diagnostic Tests', '12,000'],
        ['Nursing Charges', '6,000'],
        ['Other Hospital Charges', '6,000'],
        ['TOTAL', '₹1,25,000'],
    ]
    
    bill_table = Table(bill_data, colWidths=[4.5*inch, 2*inch])
    bill_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c62828')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffebee')),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Declaration
    story.append(Paragraph("DECLARATION", heading_style))
    declaration = """
    I hereby declare that the information provided above is true and correct to the best of my knowledge. 
    I understand that any false information may result in rejection of this claim.
    """
    story.append(Paragraph(declaration, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Signature
    sig_data = [
        ['Signature:', '_______________________'],
        ['Date:', '15/11/2024'],
        ['Place:', 'Mumbai'],
    ]
    
    sig_table = Table(sig_data, colWidths=[1.5*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    print(f"✓ Created: {filename}")

def create_hospital_bill():
    """Create a sample hospital bill"""
    filename = 'output/Hospital_Bill.pdf'
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Hospital header
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#00695c'),
        spaceAfter=10,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("APOLLO HOSPITAL", title_style))
    story.append(Paragraph("Sahar Road, Andheri East, Mumbai - 400069", 
                          ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER)))
    story.append(Paragraph("Phone: 022-XXXX-XXXX | Email: billing@apollomumbai.com", 
                          ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER)))
    story.append(Spacer(1, 0.3*inch))
    
    # Bill header
    story.append(Paragraph("FINAL HOSPITAL BILL", 
                          ParagraphStyle('BillTitle', parent=styles['Heading2'], 
                                       fontSize=16, textColor=colors.HexColor('#00695c'), alignment=TA_CENTER)))
    story.append(Spacer(1, 0.2*inch))
    
    # Patient details
    patient_data = [
        ['Bill Number:', 'APL-MUM-2024-5678'],
        ['Patient Name:', 'Rajesh Kumar Sharma'],
        ['Age/Gender:', '39 Years / Male'],
        ['Patient ID:', 'PAT-456789'],
        ['Admission Date:', '10/11/2024 - 08:30 AM'],
        ['Discharge Date:', '13/11/2024 - 11:00 AM'],
        ['Total Days:', '3 Days'],
        ['Doctor:', 'Dr. Amit Patel (General Surgeon)'],
        ['Department:', 'General Surgery'],
    ]
    
    patient_table = Table(patient_data, colWidths=[2*inch, 4.5*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0f2f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Detailed bill
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#00695c'),
        spaceAfter=10
    )
    
    story.append(Paragraph("DETAILED BILL", heading_style))
    
    detailed_bill = [
        ['S.No', 'Description', 'Quantity', 'Rate (₹)', 'Amount (₹)'],
        ['1', 'Room Charges (Semi-Private AC)', '3 days', '2,500', '7,500'],
        ['2', 'Laparoscopic Appendectomy', '1', '45,000', '45,000'],
        ['3', 'Surgeon Professional Fees', '1', '25,000', '25,000'],
        ['4', 'Anesthesia Charges', '1', '8,000', '8,000'],
        ['5', 'OT Charges', '1', '12,000', '12,000'],
        ['6', 'Medicines', '-', '-', '15,500'],
        ['7', 'Injections and IV Fluids', '-', '-', '8,500'],
        ['8', 'Blood Tests (CBC, LFT, etc.)', '-', '-', '3,500'],
        ['9', 'Ultrasound Abdomen', '1', '2,000', '2,000'],
        ['10', 'X-Ray Chest', '1', '800', '800'],
        ['11', 'ECG', '1', '500', '500'],
        ['12', 'Nursing Charges', '3 days', '2,000', '6,000'],
        ['13', 'Consumables', '-', '-', '4,200'],
        ['14', 'Registration Charges', '1', '500', '500'],
        ['', '', '', 'SUB-TOTAL:', '₹1,39,000'],
        ['', '', '', 'Hospital Discount (10%):', '-₹14,000'],
        ['', '', '', 'TOTAL PAYABLE:', '₹1,25,000'],
    ]
    
    detailed_table = Table(detailed_bill, colWidths=[0.5*inch, 3*inch, 1*inch, 1*inch, 1.5*inch])
    detailed_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00695c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -3), 1, colors.grey),
        ('LINEABOVE', (0, -3), (-1, -3), 2, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0f2f1')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
    ]))
    story.append(detailed_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Payment info
    story.append(Paragraph("PAYMENT INFORMATION", heading_style))
    payment = """
    <b>Amount Paid:</b> ₹1,25,000<br/>
    <b>Payment Mode:</b> Insurance Claim (SecureHealth Insurance)<br/>
    <b>Payment Date:</b> 13/11/2024<br/>
    <b>Status:</b> PAID
    """
    story.append(Paragraph(payment, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Footer
    story.append(Paragraph("Thank you for choosing Apollo Hospital. Wishing you good health!", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                                       textColor=colors.grey, alignment=TA_CENTER)))
    
    doc.build(story)
    print(f"✓ Created: {filename}")

def create_discharge_summary():
    """Create a sample discharge summary"""
    filename = 'output/Discharge_Summary.pdf'
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Header
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1565c0'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("DISCHARGE SUMMARY", title_style))
    story.append(Paragraph("Apollo Hospital, Mumbai", 
                          ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)))
    story.append(Spacer(1, 0.3*inch))
    
    # Patient info
    patient_info = [
        ['Patient Name:', 'Rajesh Kumar Sharma', 'Age/Gender:', '39 Yrs / Male'],
        ['Patient ID:', 'PAT-456789', 'Admission Date:', '10/11/2024'],
        ['Discharge Date:', '13/11/2024', 'Total Stay:', '3 Days'],
    ]
    
    patient_table = Table(patient_info, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e3f2fd')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Medical details
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1565c0'),
        spaceAfter=8,
        spaceBefore=10
    )
    
    story.append(Paragraph("DIAGNOSIS", heading_style))
    story.append(Paragraph("Acute Appendicitis with peritonitis", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("PROCEDURE PERFORMED", heading_style))
    story.append(Paragraph("Laparoscopic Appendectomy under General Anesthesia", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("CLINICAL SUMMARY", heading_style))
    clinical = """
    Patient presented to emergency department with complaints of severe abdominal pain in right lower quadrant 
    for 12 hours, associated with nausea and vomiting. On examination, patient was febrile (101.2°F) with 
    tenderness and guarding in right iliac fossa. McBurney's point tenderness was positive. Blood investigations 
    showed elevated WBC count (14,500/cumm). Ultrasound abdomen confirmed acute appendicitis. Patient was 
    taken up for emergency laparoscopic appendectomy. Procedure was uneventful. Post-operative recovery was 
    satisfactory.
    """
    story.append(Paragraph(clinical, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("CONDITION AT DISCHARGE", heading_style))
    story.append(Paragraph("Stable, afebrile, wound healing well", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("MEDICATIONS ON DISCHARGE", heading_style))
    meds = """
    1. Tab. Amoxicillin + Clavulanic Acid 625mg - TDS for 5 days<br/>
    2. Tab. Diclofenac 50mg - SOS for pain<br/>
    3. Tab. Pantoprazole 40mg - OD for 7 days<br/>
    4. Syrup Lactulose 15ml - HS for 5 days
    """
    story.append(Paragraph(meds, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("ADVICE ON DISCHARGE", heading_style))
    advice = """
    1. Keep surgical wound clean and dry<br/>
    2. Avoid heavy lifting for 2 weeks<br/>
    3. Light diet for 3-4 days, then normal diet<br/>
    4. Follow-up after 7 days for suture removal<br/>
    5. Report immediately if fever, wound discharge, or severe pain
    """
    story.append(Paragraph(advice, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Doctor signature
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Dr. Amit Patel", 
                          ParagraphStyle('Sign', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold')))
    story.append(Paragraph("MS (General Surgery)", styles['Normal']))
    story.append(Paragraph("Registration No: MH-12345", styles['Normal']))
    story.append(Paragraph("Date: 13/11/2024", styles['Normal']))
    
    doc.build(story)
    print(f"✓ Created: {filename}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Creating Sample Health Insurance Documents")
    print("="*60 + "\n")
    
    create_health_insurance_policy()
    create_claim_form()
    create_hospital_bill()
    create_discharge_summary()
    
    print("\n" + "="*60)
    print("✓ All sample documents created successfully!")
    print("="*60)
    print("\nDocuments saved in: sample_documents/output/")
    print("\nYou can now upload these documents to test the system:")
    print("  1. Health_Insurance_Policy.pdf")
    print("  2. Health_Insurance_Claim_Form.pdf")
    print("  3. Hospital_Bill.pdf")
    print("  4. Discharge_Summary.pdf")
    print("\n")
