# API Client Fixes - Status 400 & Pending Records

## 🎯 **Issues Fixed**

### 1. ⚠️ **Status 400 "Too Many Results" Error**
**Problem**: API returns status 400 with "Found more than twenty five eiendoms" error
**Solution**: Special handling for this specific error case

```python
# Now detects and handles the specific error:
if response.status_code == 400:
    error_data = response.json()
    if "more than twenty five" in error_message:
        return "TOO_MANY_RESULTS"  # Special status
```

**Status Message**: `"Too many results (25+ eiendommer)"`
**Records Returned**: `0`

### 2. 🔄 **Pending Records Issue**
**Problem**: Interrupted processing leaves "Pending" records that get reprocessed
**Solution**: Enhanced stored procedure + automatic cleanup

#### **Updated Stored Procedure Logic**:
```sql
-- Exclude certificates that are:
-- 1. Already successfully processed (any non-Pending status)
-- 2. Currently being processed (Pending status less than 1 hour old)
AND NOT EXISTS (
    SELECT 1 FROM [ev_enova].[EnovaApi_Energiattest_url_log] EU
    WHERE EU.[CertificateID] = IH.[CertificateID]
      AND EU.status_message != 'Pending'  -- Successfully processed
)
AND NOT EXISTS (
    SELECT 1 FROM [ev_enova].[EnovaApi_Energiattest_url_log] EU
    WHERE EU.[CertificateID] = IH.[CertificateID]
      AND EU.status_message = 'Pending'
      AND EU.LogDate > DATEADD(HOUR, -1, GETDATE())  -- Recent pending
)
```

#### **Automatic Cleanup**:
- Cleans up stale pending records (older than 1 hour) before each run
- Manual cleanup command available

## 🚀 **Enhanced Features**

### **New Status Messages**:
1. `"Success"` - API call successful, data saved
2. `"No records found"` - API returned empty result
3. `"Too many results (25+ eiendommer)"` - API returned 25+ results error
4. `"Error: [details]"` - API call or processing failed
5. `"API returned data but no records saved"` - Data returned but DB save failed

### **New Commands**:
```bash
# Clean up old pending records
python main.py cleanup --hours 24        # Clean records older than 24 hours
python main.py cleanup --hours 1         # Clean records older than 1 hour

# Process with automatic cleanup
python main.py api --rows 10             # Automatically cleans up before processing
```

### **Enhanced Processing Logic**:
1. **Pre-processing**: Automatic cleanup of stale pending records
2. **Smart exclusion**: Won't reprocess certificates from interrupted runs
3. **Status tracking**: Detailed status for every API outcome
4. **Error handling**: Special handling for "too many results" error

## 📊 **Status Breakdown Examples**

### **Before Fix**:
```
✓ API processing completed successfully
  Parameters logged: 5
  API calls made: 5
  Records inserted: 8
```

### **After Fix**:
```
✓ API processing completed successfully
  Parameters logged: 5
  API calls made: 5
  Records inserted: 8
  Processing time: 2.347 seconds

📊 Status breakdown:
    Success: 3 calls → 8 records returned
    No records found: 1 calls → 0 records returned
    Too many results (25+ eiendommer): 1 calls → 0 records returned
```

## 🔧 **Implementation Details**

### **API Client Changes**:
- Enhanced `call_energiattest_api()` with 400 status detection
- Added `cleanup_old_pending_records()` method
- Updated `process_certificates()` with automatic cleanup
- Improved status tracking and reporting

### **Database Changes**:
- Updated stored procedure `[ev_enova].[Get_Enova_API_Parameters]`
- Smart exclusion logic for pending records
- Enhanced monitoring capabilities

### **CLI Enhancements**:
- New `cleanup` command for manual cleanup
- Enhanced status reporting in `api` command
- Better error handling and user feedback

## 🎯 **Usage Examples**

```bash
# Normal processing (with automatic cleanup)
python main.py api --rows 10

# Manual cleanup of old pending records
python main.py cleanup --hours 1

# Test with detailed output
python tests/test_api_client.py --rows 3 --full
```

## 🔍 **Monitoring**

Use the monitoring queries in `sql/monitoring_queries.sql` to track:
- Status distribution and success rates
- Pending records that need cleanup
- "Too many results" occurrences
- Processing performance trends

## ✅ **Result**

- **No more duplicate processing** of interrupted runs
- **Special handling** for "too many results" API errors  
- **Automatic cleanup** of stale pending records
- **Enhanced visibility** into all processing outcomes
- **Better error handling** and user feedback

Your API client now handles both the 400 status "too many results" error and properly manages pending records from interrupted runs! 🎉
