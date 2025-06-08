# ChemScreen User Guide

## Welcome to ChemScreen

ChemScreen is a powerful tool designed to help librarians and regulatory professionals quickly screen large batches of chemicals for literature evidence. Instead of manually searching for each chemical one-by-one (which can take 2-3 days for 50-100 chemicals), ChemScreen automates the process and completes the same work in 2-3 hours.

## Quick Start

### What You Need

- A CSV file with your chemical names and CAS numbers
- 5-10 minutes to upload and configure your search
- An internet connection for PubMed searches

### Basic Workflow

1. **Upload** your chemical list
2. **Configure** search parameters
3. **Start** the automated search
4. **Review** results and quality scores
5. **Export** formatted reports

Let's walk through each step in detail.

## Step 1: Preparing Your Chemical List

### File Format

ChemScreen accepts CSV (comma-separated values) files with the following format:

```csv
Chemical Name,CAS Number
Caffeine,58-08-2
Aspirin,50-78-2
Glucose,50-99-7
Benzene,71-43-2
```

### Required Information

- **Chemical Name** (required): Common name, IUPAC name, or trade name
- **CAS Number** (optional but recommended): Chemical Abstracts Service registry number

### Creating Your CSV File

**From Excel**:
1. Create two columns: "Chemical Name" and "CAS Number"
2. Enter your chemicals (one per row)
3. Save as "CSV (Comma delimited)" format

**From Google Sheets**:
1. Create your chemical list in the same format
2. File → Download → Comma-separated values (.csv)

**Tips for Better Results**:
- ✅ Use standard chemical names when possible
- ✅ Include CAS numbers for accuracy
- ✅ Check spelling of chemical names
- ✅ One chemical per row
- ❌ Avoid special characters in chemical names
- ❌ Don't include extra columns (ChemScreen uses first two columns only)

### File Size Limits

- **Maximum file size**: 10 MB
- **Recommended batch size**: 25-100 chemicals
- **For larger lists**: Split into multiple files for better performance

## Step 2: Uploading Your File

### Upload Process

1. **Drag and drop** your CSV file onto the upload area, or
2. **Click "Browse files"** to select your file

### File Preview

After uploading, ChemScreen will show you a preview of your chemicals:
- **Chemical names** as they will be searched
- **CAS numbers** (if provided)
- **Validation status** for each entry

### Common Upload Issues

#### File format not supported

- Ensure your file is saved as .csv format
- Try re-saving from Excel as "CSV (Comma delimited)"

#### File too large

- Split large lists into smaller batches (50-100 chemicals per file)
- Remove unnecessary columns

#### No chemicals detected

- Check that your first row contains headers
- Ensure chemical names are in the first column

## Step 3: Configuring Search Parameters

### Search Parameters

**Date Range** (Default: 10 years)
- How far back to search for publications
- Options: 3, 5, 10, 15, or 20 years
- *Recommendation*: Use 10 years for comprehensive screening

**Include Review Articles** (Default: Yes)
- Whether to include review articles in results
- Reviews often provide comprehensive overviews
- *Recommendation*: Include reviews for complete picture

**Maximum Results per Chemical** (Default: 100)
- Limits the number of publications retrieved per chemical
- Higher numbers = more comprehensive but slower
- *Recommendation*: 50-100 for most regulatory work

**Use Cache** (Default: Yes)
- Speeds up repeat searches by saving previous results
- No impact on result quality
- *Recommendation*: Always keep enabled

### Advanced Settings

Click "Advanced Options" to access additional settings:

**Search Strategy**:
- **Comprehensive**: Searches chemical name, CAS number, and common synonyms
- **Targeted**: Searches only provided name and CAS number
- **Broad**: Includes trade names and alternative spellings

**Quality Filters**:
- **Minimum publication year**: Exclude very old publications
- **Journal quality filter**: Focus on peer-reviewed journals
- **Language filter**: English-only or all languages

## Step 4: Running Your Search

### Starting the Search

1. Review your uploaded chemicals in the preview
2. Adjust search parameters if needed
3. Click **"Start Literature Search"**

### Monitoring Progress

ChemScreen will show real-time progress:
- **Progress bar**: Overall completion percentage
- **Current chemical**: Which chemical is being searched
- **Status updates**: Search progress and any issues
- **Time estimate**: Approximate time remaining

### What Happens During Search

For each chemical, ChemScreen:

1. Builds optimized PubMed search queries
2. Retrieves publication lists from PubMed
3. Calculates quality scores and metrics
4. Caches results for future use

### Expected Timing

- **10 chemicals**: 2-5 minutes
- **50 chemicals**: 10-20 minutes
- **100 chemicals**: 20-40 minutes

*Note: Times depend on internet speed and PubMed responsiveness*

### If Something Goes Wrong
- **Slow progress**: Normal for large batches; PubMed rate limits apply
- **Individual chemical errors**: ChemScreen will note these and continue
- **Complete failure**: Check internet connection and try smaller batches

## Step 5: Understanding Your Results

### Results Overview
After completion, you'll see a summary table with:
- **Chemical Name**: As searched
- **CAS Number**: If provided
- **Total Publications**: Number of articles found
- **Recent Publications**: Articles from last 3 years
- **Quality Score**: 0-100 scale indicating literature strength
- **Publication Trend**: Increasing, stable, or decreasing research activity
- **Review Status**: Whether recent reviews are available

### Quality Score Interpretation

**High Quality (70-100)**:
- Abundant literature available
- Recent research activity
- Multiple types of studies
- Good for comprehensive assessment

**Medium Quality (40-69)**:
- Moderate literature base
- Some recent activity
- May need focused searching for specific endpoints
- Good starting point for assessment

**Low Quality (0-39)**:
- Limited literature available
- Little recent research
- May require alternative search strategies
- Consider manual verification

### Publication Trends

**📈 Increasing**: Growing research interest, new studies available
**📊 Stable**: Consistent research output over time
**📉 Decreasing**: Declining research interest, mostly older studies

### Sorting and Filtering Results

#### Sort by

- **Quality Score**: Prioritize chemicals with strong literature
- **Publication Count**: Focus on well-studied chemicals
- **Recent Activity**: Identify chemicals with new research

#### Filter by

- **Quality threshold**: Show only high-quality results
- **Publication count**: Focus on chemicals above/below certain thresholds
- **Error status**: Review chemicals that had search issues

### Individual Chemical Details

Click on any chemical name to see detailed information:
- **Complete publication list** with titles and authors
- **Search parameters used**
- **Publication breakdown by year**
- **Journal distribution**
- **Review article highlights**

## Step 6: Exporting Your Results

### Export Formats

#### Excel (.xlsx) - Recommended

- Multiple worksheets with organized data
- Summary sheet with key metrics
- Detailed results with full publication information
- Search metadata and parameters
- Formatted for easy analysis

#### CSV (.csv)

- Single file with all results
- Easy to import into other tools
- Good for further data analysis
- Compatible with all spreadsheet software

#### JSON (.json)

- Complete data in structured format
- Suitable for technical users
- Preserves all search metadata
- Good for integration with other systems

### Export Options

**Include Abstracts**:
- ✅ Yes: Complete publication details including abstracts
- ❌ No: Summary information only (smaller file size)

**File Naming**:
- Files automatically named with date and batch ID
- Format: `chemscreen_export_YYYYMMDD_batchID.xlsx`

### Using Your Exported Data

#### Excel Workflow

1. Open the exported Excel file
2. **Summary sheet**: Overview of all chemicals with key metrics
3. **Detailed Results**: Complete publication data
4. **Search Metadata**: Parameters used and search information
5. Add your own columns for notes, priority levels, or assessment status

#### Integration with Other Tools

- Import CSV data into regulatory databases
- Copy publication lists into reference managers
- Use PMIDs to download full-text articles
- Create custom reports for stakeholders

### File Management
- **Automatic naming**: Files include timestamp and batch ID
- **Download location**: Check your browser's download folder
- **Storage recommendation**: Organize by project or assessment date

## Advanced Features

### Session Management

#### Session History

- View previous searches
- Resume interrupted sessions
- Compare results across different parameters

#### Session Recovery

- If your browser closes, return to see previous results
- Sessions automatically saved during processing
- Can export results from previous sessions

### Batch Management

#### Multiple Batches

- Process multiple chemical lists separately
- Compare results across different chemical sets
- Maintain separate projects or assessments

#### Optimal Batch Sizes

- **Small batches (10-25)**: Quick testing or high-priority chemicals
- **Medium batches (25-75)**: Typical regulatory screening
- **Large batches (75-200)**: Comprehensive assessments

### Cache Benefits

#### Speed Improvements

- Repeat searches are nearly instantaneous
- Useful for testing different parameters
- Shared cache benefits team members

#### Cache Management

- Automatically cleans old entries
- No action needed from users
- Can be manually cleared if needed

## Regulatory Applications

### TSCA Screening

#### Typical Workflow

1. Upload PMN chemical list
2. Use 10-year search range
3. Include reviews for comprehensive coverage
4. Focus on toxicology and environmental fate literature
5. Export for risk assessment documentation

#### Key Metrics to Review

- Recent toxicology studies
- Environmental fate and transport data
- Exposure assessment information
- Ecological effects literature

### REACH Assessment

#### Typical Workflow
1. Upload SVHC candidate list
2. Use 5-year search for recent activity
3. Include reviews for regulatory summaries
4. Look for endocrine disruption and PBT data
5. Export for dossier preparation

**Key Metrics to Review**:
- PBT assessment data
- Endocrine disruption studies
- Ecotoxicology information
- Human health effects

### Pesticide Registration
**Typical Workflow**:
1. Upload active ingredient list
2. Use comprehensive search (15-20 years)
3. Include reviews for registration summaries
4. Focus on environmental and health effects
5. Export for EPA submission documentation

**Key Metrics to Review**:
- Residue studies
- Environmental fate studies
- Non-target organism effects
- Resistance management literature

## Best Practices

### Preparing Chemical Lists

**Data Quality**:
- Verify chemical names before uploading
- Use IUPAC names when possible
- Include CAS numbers for accuracy
- Remove duplicates from your list

**Batch Planning**:
- Group related chemicals together
- Consider assessment timelines when sizing batches
- Plan for manual follow-up on low-quality results

### Search Strategy

**Parameter Selection**:
- Start with default parameters for most work
- Adjust date range based on chemical age and research timeline
- Include reviews unless specifically focused on primary research
- Use comprehensive search strategy for initial screening

**Quality Assurance**:
- Review chemicals with unexpectedly low publication counts
- Manually verify results for critical chemicals
- Consider alternative search terms for poor results

### Results Interpretation

**Prioritization**:
- High-quality chemicals: Proceed with standard literature review
- Medium-quality chemicals: May need focused manual searching
- Low-quality chemicals: Consider alternative data sources

**Documentation**:
- Save search parameters for reproducibility
- Document any manual verification performed
- Include ChemScreen results in assessment methodology

### Integration with Existing Workflows

**Literature Review Process**:
1. Use ChemScreen for initial screening and prioritization
2. Focus manual effort on high-priority chemicals
3. Use PMIDs from ChemScreen to download full texts
4. Supplement with targeted manual searches as needed

**Team Collaboration**:
- Share exported results with team members
- Use consistent search parameters across projects
- Maintain central repository of ChemScreen exports

## Troubleshooting

### Common Issues

**No Results for Chemical**:
- Check chemical name spelling
- Try alternative names or synonyms
- Verify CAS number if provided
- Consider that some chemicals may have limited literature

#### Low Quality Scores

- Normal for new or specialty chemicals
- Consider broadening search parameters
- May require manual literature searching
- Check for alternative chemical names

#### Slow Performance

- Reduce batch size (try 25-50 chemicals)
- Check internet connection
- Process during off-peak hours
- Contact support if consistently slow

#### Export Issues

- Ensure browser allows downloads
- Check available disk space
- Try alternative export format (CSV vs Excel)
- Refresh page and try export again

### Getting Help

#### Built-in Help

- Hover over question marks (?) for field explanations
- Check status messages during processing
- Review error messages for specific guidance

#### Documentation

- This user guide covers most common scenarios
- Check FAQ section for additional tips
- Review example workflows for your field

#### Technical Support

- Use the feedback button to report issues
- Include error messages and browser information
- Describe your workflow and expected results

## Tips for Success

### Efficiency Tips
- **Start small**: Test with 10-20 chemicals first
- **Use defaults**: Standard parameters work for most cases
- **Plan batches**: Group related chemicals together
- **Enable cache**: Speeds up repeat searches significantly

### Quality Tips
- **Verify names**: Double-check chemical spelling
- **Include CAS**: Improves search accuracy
- **Review results**: Manually check surprising results
- **Document process**: Save parameters and methodology

### Workflow Tips
- **Regular exports**: Download results promptly
- **Organize files**: Use consistent naming for projects
- **Share results**: Export formats work well for collaboration
- **Follow up**: Use results to guide focused manual searching

## Frequently Asked Questions

**Q: How accurate are the search results?**
A: ChemScreen uses the same PubMed database that librarians search manually. Results are as comprehensive as manual searching but much faster. Quality scores help identify chemicals that may need additional manual verification.

**Q: Can I search for trade names or synonyms?**
A: Yes, ChemScreen includes common synonyms in its searches. For best results, provide the most common or official chemical name. You can also upload multiple entries for the same chemical with different names.

**Q: How current are the search results?**
A: ChemScreen searches the live PubMed database, so results include publications up to the current date. The database is updated daily by the National Library of Medicine.

**Q: What if I need to search other databases besides PubMed?**
A: ChemScreen currently focuses on PubMed, which contains the majority of biomedical and life sciences literature. For specialized databases (e.g., toxicology, environmental), use ChemScreen results as a starting point and supplement with targeted manual searches.

**Q: Can I save my search parameters for future use?**
A: Yes, ChemScreen remembers your last-used parameters. For consistent workflows, document your standard parameters and use them across similar projects.

**Q: How long are results cached?**
A: Cache entries are stored for 1 hour by default. This means repeat searches for the same chemicals with identical parameters will be much faster.

**Q: Can multiple people use the same ChemScreen instance?**
A: Yes, ChemScreen can be accessed by multiple users simultaneously. Each user's session is independent, so you won't interfere with others' searches.

**Q: What should I do if a chemical returns no results?**
A: This can happen with very new chemicals, specialized industrial chemicals, or misspelled names. Try alternative names, check spelling, or consider that some chemicals genuinely have limited published literature.

## Conclusion

ChemScreen transforms the chemical literature screening process from a time-intensive manual task into an efficient automated workflow. By following this guide, you can quickly become proficient in using ChemScreen to support your regulatory assessment and literature review work.

Remember that ChemScreen is designed to complement, not replace, professional expertise in literature evaluation. Use the tool to efficiently identify and prioritize chemicals for further assessment, then apply your professional judgment to interpret and act on the results.

For additional support or to provide feedback on this guide, use the feedback mechanisms built into the application or contact your system administrator.

---

**Need Help?** Click the "Help" button in the ChemScreen interface or refer to the troubleshooting section above.

**Version**: 1.0
**Last Updated**: [Current Date]
