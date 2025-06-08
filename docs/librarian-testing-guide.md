# Librarian Testing Guide

## Overview

This guide helps librarians test ChemScreen to ensure it meets the needs of regulatory assessment support. The goal is to validate that the tool reduces chemical literature screening time from 2-3 days to 2-3 hours for batches of 50-100+ chemicals.

## Getting Started

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for PubMed searches
- No software installation required

### Accessing ChemScreen

1. Open your web browser
2. Navigate to the ChemScreen application URL
3. You should see the main interface with upload area

## Testing Scenarios

### Scenario 1: Small Batch Quick Test (10 chemicals)

**Objective**: Verify basic functionality with a small, manageable set of chemicals.

**Steps**:
1. **Upload File**: Use the "demo_small.csv" file (should be provided)
2. **Review Preview**:
   - [ ] All 10 chemicals appear in the preview table
   - [ ] Chemical names look correct
   - [ ] CAS numbers are present where expected
3. **Configure Search**:
   - Leave default settings (10 years, include reviews, 100 max results)
   - [ ] Settings are clearly explained
4. **Start Search**:
   - [ ] Progress bar updates regularly
   - [ ] Status messages are informative
   - [ ] Search completes within 5 minutes
5. **Review Results**:
   - [ ] Results table shows publication counts
   - [ ] Quality scores are displayed
   - [ ] No major errors reported

**Success Criteria**:
- All chemicals return some results
- Process completes without errors
- Results are understandable

### Scenario 2: Medium Batch Realistic Test (50 chemicals)

**Objective**: Test with a realistic workload similar to daily regulatory work.

**Steps**:
1. **Upload File**: Use the "demo_medium.csv" file
2. **Review Chemical List**:
   - [ ] Preview shows manageable number of rows
   - [ ] Can scroll through full list
   - [ ] Chemical names are recognizable
3. **Configure Search Parameters**:
   - Try different date ranges (5 years, 10 years)
   - Test with and without reviews
   - [ ] Settings affect search scope appropriately
4. **Monitor Search Progress**:
   - [ ] Progress updates every few chemicals
   - [ ] Time estimates are reasonable
   - [ ] Can continue other work while running
5. **Analyze Results**:
   - [ ] Can sort by publication count
   - [ ] Can sort by quality score
   - [ ] Can identify high-priority chemicals easily

**Success Criteria**:
- Search completes within 20 minutes
- Results help prioritize chemical reviews
- No chemicals lost due to errors

### Scenario 3: Real-World Workflow Test

**Objective**: Simulate actual regulatory assessment workflow.

**Your Chemical List**:
Use a real list of 20-30 chemicals from current work (remove sensitive information).

**Workflow Steps**:
1. **Prepare Data**:
   - Create CSV with your chemicals
   - Include CAS numbers where available
   - [ ] Upload process is straightforward
2. **Search Strategy**:
   - Start with 3-year search for recent activity
   - Include reviews for comprehensive coverage
   - [ ] Parameter choices make sense for your needs
3. **Results Triage**:
   - Identify chemicals with high publication counts
   - Look for chemicals with recent reviews
   - Note chemicals with few/no results
   - [ ] Quality scores help prioritize effort
4. **Export and Use**:
   - Export results to Excel
   - [ ] File opens correctly in Excel
   - [ ] Data is formatted for further analysis
   - [ ] Can add your own notes/columns

**Success Criteria**:
- Saves significant time vs. manual searching
- Results are actionable for regulatory assessment
- Export integrates with existing workflows

### Scenario 4: Error Handling and Edge Cases

**Objective**: Test how the system handles problematic data and situations.

**Test Cases**:

1. **Invalid Chemical Names**:
   - Upload file with misspelled chemicals
   - [ ] System provides helpful feedback
   - [ ] Can proceed with valid chemicals

2. **Missing CAS Numbers**:
   - Test chemicals without CAS numbers
   - [ ] System still finds relevant results
   - [ ] No crashes or errors

3. **Network Issues**:
   - Test during slow internet periods
   - [ ] System handles timeouts gracefully
   - [ ] Can retry failed searches

4. **Large File Upload**:
   - Test with 100+ chemical file
   - [ ] Upload completes successfully
   - [ ] Memory usage remains stable

**Success Criteria**:
- System degrades gracefully under problems
- Error messages are helpful, not technical
- Can recover from most issues

### Scenario 5: Export and Reporting

**Objective**: Verify that exported data meets documentation needs.

**Export Testing**:
1. **Excel Export**:
   - [ ] Multiple worksheets with logical organization
   - [ ] Summary sheet with key metrics
   - [ ] Detailed results with full publication data
   - [ ] Metadata sheet with search parameters
2. **CSV Export**:
   - [ ] Can be opened in Excel
   - [ ] Data is properly formatted
   - [ ] Suitable for further analysis
3. **Format Comparison**:
   - [ ] Same data in both formats
   - [ ] Can choose based on needs

**Content Verification**:
- [ ] Chemical names and CAS numbers preserved
- [ ] Publication counts accurate
- [ ] Quality scores explained
- [ ] Search parameters documented
- [ ] Export timestamp included

**Integration Testing**:
- [ ] Can import into existing tracking systems
- [ ] Format works with regulatory templates
- [ ] Suitable for sharing with colleagues

## Usability Evaluation

### Interface Assessment

**Ease of Use** (Rate 1-5, 5 = Excellent):
- File upload process: ___
- Parameter configuration: ___
- Progress monitoring: ___
- Results interpretation: ___
- Export functionality: ___

**Clarity** (Rate 1-5, 5 = Very Clear):
- Instructions and labels: ___
- Error messages: ___
- Progress indicators: ___
- Results presentation: ___
- Help information: ___

### Workflow Integration

**Questions to Consider**:
1. How does this fit into your current chemical screening process?
2. What information is missing that you usually need?
3. How would you modify the output for your reports?
4. What additional features would be helpful?
5. Would this tool reduce your screening time significantly?

### Performance Feedback

**Time Comparison**:
- Manual search time for 50 chemicals: ___ hours
- ChemScreen time for 50 chemicals: ___ minutes
- Time savings: ___%

**Quality Assessment**:
- Are important publications being found? Yes/No
- Are results comprehensive enough? Yes/No
- Would you trust these results for initial screening? Yes/No
- What would you verify manually afterward?

## Common Issues and Solutions

### Upload Problems

- **Issue**: CSV file won't upload
- **Solution**: Check file format, ensure UTF-8 encoding
- **Workaround**: Try saving from Excel as "CSV (Comma delimited)"

### Slow Performance

- **Issue**: Searches taking too long
- **Solution**: Try smaller batches (25-50 chemicals)
- **Workaround**: Run searches during off-peak hours

### Missing Results

- **Issue**: Some chemicals return no results
- **Reasons**:
  - Very new or obscure chemicals
  - Misspelled names
  - Alternative nomenclature needed
- **Solution**: Try alternative chemical names or synonyms

### Export Issues

- **Issue**: Excel file won't open properly
- **Solution**: Ensure Excel can handle .xlsx format
- **Workaround**: Use CSV export if Excel export fails

## Feedback Collection

### Critical Issues (Must Fix)

List any issues that prevent effective use:
1. ____________________
2. ____________________
3. ____________________

### Important Improvements (Should Fix)

List issues that reduce efficiency:
1. ____________________
2. ____________________
3. ____________________

### Nice-to-Have Features (Could Add)

List features that would enhance workflow:
1. ____________________
2. ____________________
3. ____________________

### Overall Assessment

**Would you use this tool for regulatory chemical screening?**
- [ ] Yes, as-is
- [ ] Yes, with minor improvements
- [ ] Yes, but needs significant improvements
- [ ] No, not suitable for our needs

**Primary Benefits**:
1. ____________________
2. ____________________
3. ____________________

**Primary Concerns**:
1. ____________________
2. ____________________
3. ____________________

**Recommendation for Implementation**:
- [ ] Ready for production use
- [ ] Needs testing improvements first
- [ ] Requires major changes
- [ ] Not recommended

## Regulatory-Specific Testing

### TSCA Screening Workflow
If you work with TSCA assessments:
1. Test with PMN chemicals
2. Verify recent toxicology studies are found
3. Check environmental fate publications
4. Ensure exposure assessment literature appears

### REACH Assessment Workflow
If you work with REACH:
1. Test with SVHC candidates
2. Look for endocrine disruption studies
3. Check for PBT assessment data
4. Verify ecotoxicology results

### Pesticide Registration
If you work with pesticides:
1. Test with active ingredients
2. Look for residue studies
3. Check for ecological impact research
4. Verify resistance management literature

## Advanced Features Testing

### Search Refinement
- Test different date ranges for trending analysis
- Compare results with/without reviews
- Experiment with result limits

### Quality Scoring
- Understand what makes a high vs. low quality score
- Test if scores align with your professional judgment
- Note chemicals that might need manual review despite scores

### Batch Management
- Test with multiple small batches vs. one large batch
- Compare performance and results
- Determine optimal batch sizes for your workflow

## Documentation Requirements

### For Management Reports
Verify that exports include:
- [ ] Clear methodology description
- [ ] Search parameters and dates
- [ ] Summary statistics
- [ ] Individual chemical results
- [ ] Quality indicators

### For Peer Review
Ensure documentation supports:
- [ ] Reproducible searches
- [ ] Parameter justification
- [ ] Results verification
- [ ] Follow-up recommendations

### For Regulatory Submissions

Check that data can support:
- [ ] Literature search documentation
- [ ] Systematic review protocols
- [ ] Data gap identification
- [ ] Priority setting justification

## Final Recommendations

Based on your testing, provide recommendations for:

1. **Immediate Use**: What can be used right away?
2. **Required Improvements**: What must be fixed before broader adoption?
3. **Training Needs**: What training would help other librarians?
4. **Integration Plan**: How to incorporate into existing workflows?
5. **Success Metrics**: How to measure improved efficiency?

---

**Testing Completed By**: ________________
**Date**: ________________
**Organization**: ________________
**Experience Level**: ________________

Thank you for your thorough testing and feedback!
