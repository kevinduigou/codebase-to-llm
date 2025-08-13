# File & Directory Manager Test Interface

This document explains how to use the comprehensive web UI for testing all file and directory management routes in the application.

## Access the Test Interface

Once the application is running, you can access the test interface at:
```
http://localhost:8000/file-manager-test
```

## Features

### Authentication
- The interface requires user authentication
- If not logged in, you'll be redirected to the login page
- Once authenticated, you can access all testing features

### File Management Testing

#### 1. Upload File (POST /files)
- **File ID**: Unique identifier for the file
- **File Name**: Display name for the file
- **Directory ID**: Optional - ID of parent directory
- **File Content**: Text content of the file

#### 2. Get File (GET /files/{file_id})
- Retrieve file information and content by ID
- Shows file metadata and content

#### 3. Update File (PUT /files/{file_id})
- **File ID**: ID of file to update
- **New Name**: Optional new name for the file
- **New Directory ID**: Optional new parent directory

#### 4. Delete File (DELETE /files/{file_id})
- Delete a file by its ID
- Confirmation dialog prevents accidental deletion

### Directory Management Testing

#### 1. Create Directory (POST /directories)
- **Directory ID**: Unique identifier for the directory
- **Directory Name**: Display name for the directory
- **Parent ID**: Optional - ID of parent directory for nested structure

#### 2. Get Directory (GET /directories/{directory_id})
- Retrieve directory information by ID
- Shows directory metadata and parent relationship

#### 3. Update Directory (PUT /directories/{directory_id})
- **Directory ID**: ID of directory to update
- **New Name**: Optional new name for the directory
- **New Parent ID**: Optional new parent directory

#### 4. Delete Directory (DELETE /directories/{directory_id})
- Delete a directory by its ID
- Confirmation dialog prevents accidental deletion

## Quick Actions

### Generate Sample Data
- Click "🎲 Generate Sample Data" to automatically fill forms with test data
- Generates unique IDs and sample content for quick testing

### Refresh Lists
- "🔄 Refresh Files" - Updates the files list with created files
- "🔄 Refresh Directories" - Updates the directories list with created directories

### Clear Responses
- "🧹 Clear All Responses" - Clears all API response displays

## Response Display

- **Success responses** are displayed with green borders and formatting
- **Error responses** are displayed with red borders and error details
- All responses are formatted as JSON for easy reading
- Response areas are scrollable for long content

## File and Directory Lists

- Shows all files and directories created during the session
- Each item displays:
  - Name and ID
  - Parent directory (for files and nested directories)
  - Quick action buttons (View, Edit, Delete)

### Quick Actions from Lists
- **View**: Automatically fills the "Get" form and executes the request
- **Edit**: Pre-fills the "Update" form with current values
- **Delete**: Shows confirmation dialog and executes deletion

## Navigation

- **Tabs**: Switch between Files and Directories sections
- **Account Menu**: Access user info and logout
- **Main Interface**: Link back to the main application interface

## Testing Workflow

1. **Start with Directories**: Create a directory structure first
2. **Create Files**: Upload files, optionally assigning them to directories
3. **Test Retrieval**: Use Get operations to verify data
4. **Test Updates**: Modify names and directory assignments
5. **Test Deletion**: Clean up test data

## API Response Codes

- **200**: Success for GET, PUT operations
- **201**: Success for POST operations (creation)
- **400**: Bad request (validation errors)
- **401**: Unauthorized (authentication required)
- **404**: Not found (invalid ID)

## Tips

- Use meaningful IDs and names for easier testing
- Test both valid and invalid scenarios
- Use the browser's developer tools to inspect network requests
- The interface maintains a local list of created items for easy management
- All operations require authentication - ensure you're logged in

## Troubleshooting

- **Authentication Errors**: Refresh the page and log in again
- **Network Errors**: Check if the backend server is running
- **Validation Errors**: Check the API response for specific error details
- **Missing Items**: Use the refresh buttons to update the lists

This test interface provides a comprehensive way to validate all file and directory management functionality without needing external tools like Postman or curl.
