# OpenAI Energy Certificate Service

This service processes energy certificate data using OpenAI's API to generate structured summaries in Norwegian.

## Overview

The `OpenAIEnergyService` takes energy certificate prompts from the database, sends them to OpenAI for analysis, and stores the structured responses back to the database.

## Required Database Tables

### Source Table: `[ev_enova].[SampleTestDataForOpenAI]`
```sql
-- Contains the prompts to be processed
CREATE TABLE [ev_enova].[SampleTestDataForOpenAI](
    [FILE_ID] [int] NOT NULL,
    [PROMPT_V1_NOR] [nvarchar](max) NULL,
    [PROMPT_V2_NOR] [nvarchar](max) NULL,
    -- Add other prompt columns as needed
)
```

### Target Table: `[ev_enova].[OpenAIAnswers]`
```sql
-- Stores the structured responses from OpenAI
CREATE TABLE [ev_enova].[OpenAIAnswers](
    [openAIAnswerID] [int] IDENTITY(1,1) NOT NULL,
    [file_id] [int] NOT NULL,
    [PromptVersion] [nvarchar](100) NOT NULL,
    [AboutEstate] [nvarchar](2000) NULL,
    [Positives] [nvarchar](2000) NULL,
    [Evaluation] [nvarchar](2000) NULL,
    [Created] [datetime] NOT NULL,
    CONSTRAINT [PK_OpenAIAnswers] PRIMARY KEY CLUSTERED ([openAIAnswerID] ASC)
)
```

## Configuration

### Environment Variables
Set these environment variables or add them to a `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.3

# Database Configuration
DATABASE_SERVER=your_server_name
DATABASE_NAME=your_database_name
DATABASE_TRUSTED_CONNECTION=yes
# OR for SQL authentication:
# DATABASE_USERNAME=your_username
# DATABASE_PASSWORD=your_password
```

## Usage

### Basic Usage

```python
from config import get_config
from src.services.openai_service import OpenAIEnergyService

# Initialize the service
config = get_config()
openai_service = OpenAIEnergyService(config)

# Process prompts from PROMPT_V1_NOR column
results = openai_service.process_prompts(
    prompt_column="PROMPT_V1_NOR",
    limit=10,  # Process only 10 records
    delay_between_calls=2.0  # 2 second delay between API calls
)

print(f"Processed: {results['prompts_processed']}")
print(f"Errors: {results['errors']}")
```

### Processing Different Prompt Versions

```python
# Process PROMPT_V1_NOR
results_v1 = openai_service.process_prompts("PROMPT_V1_NOR", limit=50)

# Process PROMPT_V2_NOR  
results_v2 = openai_service.process_prompts("PROMPT_V2_NOR", limit=50)
```

### Get Processing Statistics

```python
# Get statistics for all prompt versions
all_stats = openai_service.get_processing_statistics()

# Get statistics for specific prompt version
v1_stats = openai_service.get_processing_statistics("PROMPT_V1_NOR")

print(f"Total responses: {v1_stats['PROMPT_V1_NOR']['total_responses']}")
print(f"Completion rates: {v1_stats['PROMPT_V1_NOR']['completion_rate']}")
```

### Get Sample Responses

```python
# Get 5 sample responses for review
samples = openai_service.get_sample_responses("PROMPT_V1_NOR", limit=5)

for sample in samples:
    print(f"File ID: {sample['file_id']}")
    print(f"About Estate: {sample['about_estate'][:100]}...")
    print(f"Positives: {sample['positives'][:100]}...")
    print(f"Evaluation: {sample['evaluation'][:100]}...")
```

## Expected Response Format

The service expects OpenAI to return responses in this format:

```
Eiendom: [Description of the property]
Positive ting: [Positive aspects related to the energy certificate]
Kort vurdering: [Brief evaluation and special considerations]
```

The service automatically parses this format and stores:
- **AboutEstate**: Content after "Eiendom:"
- **Positives**: Content after "Positive ting:"
- **Evaluation**: Content after "Kort vurdering:"

## Error Handling

The service includes comprehensive error handling:

- **Database Connection Errors**: Logged and service continues with next record
- **OpenAI API Errors**: Rate limiting, timeout handling, retry logic
- **Response Parsing Errors**: Falls back to alternative parsing methods
- **Field Length Limits**: Automatically truncates responses to fit database constraints

## Rate Limiting

To respect OpenAI API limits:
- Default delay of 1.0 seconds between API calls
- Configurable delay via `delay_between_calls` parameter
- Automatic handling of 429 (rate limit) responses

## Logging

The service provides detailed logging:
- INFO level: Progress updates, statistics
- DEBUG level: API responses, parsing details
- ERROR level: Failures, exceptions
- WARNING level: Missing data, parsing issues

## Running the Example

1. Set up your environment variables
2. Ensure the database tables exist
3. Run the example script:

```bash
python example_openai_usage.py
```

## Best Practices

1. **Test with Small Batches**: Start with `limit=5` to test your setup
2. **Monitor API Usage**: OpenAI charges per token, monitor your usage
3. **Set Appropriate Delays**: Use 1-2 second delays to avoid rate limits
4. **Review Sample Responses**: Check output quality before processing large batches
5. **Handle Interruptions**: The service skips already processed records, so you can safely restart

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure OPENAI_API_KEY environment variable is set

2. **"Invalid object name 'ev_enova.SampleTestDataForOpenAI'"**
   - Verify the database schema and table names exist
   - Check database connection settings

3. **Rate limiting errors**
   - Increase `delay_between_calls` parameter
   - Reduce batch size

4. **Parsing errors**
   - The service includes fallback parsing methods
   - Check sample responses to verify OpenAI output format

### Database Connection Issues

If you get database connection errors:

1. Verify server name and database name
2. Check if using Windows Authentication or SQL Authentication
3. Ensure the database user has INSERT permissions on the target table
4. Test connection with a simple query first

## Performance Considerations

- **Batch Processing**: Process in batches of 50-100 records
- **API Limits**: OpenAI has rate limits (RPM) and token limits
- **Database**: Use connection pooling for high-volume processing
- **Monitoring**: Track success rates and adjust parameters as needed

## Sample Prompt

The service is designed to work with prompts like:

```
Opptre som ekspert i et selskap som lever av å selge informasjon om eiendom og bygninger. 
Du skal oppsummere relevante forhold knyttet til energimerke fra Enova med Energikarakter A 
og Oppvarmingskarakter Green for boligen. Merkenummer er 'Energiattest-2025-107518' datert 
April 15, 2025. Hold deg til fakta og ikke gå ut over 500 ord...

Svaret skal være på dette formatet:
Eiendom: Litt om eiendommen
Positive ting: Hva er bra i forhold til Energiattesten  
Kort vurdering: Spesielle forhold som bør trekkes frem av en eller annen art.
```
