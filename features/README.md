# Video Key Insights Behave Tests

This directory contains behavior-driven development (BDD) tests for the video key insights functionality using the Behave framework.

## Test Overview

The tests verify the complete CRUD lifecycle for video key insights:

1. **Create** - Add new video key insights to the database
2. **Read** - Retrieve video key insights by ID and list all insights
3. **Update** - (Can be extended in the future)
4. **Delete** - Remove video key insights from the database

## Test Structure

- `video_key_insights.feature` - Gherkin feature file describing the test scenarios
- `steps/video_key_insights_steps.py` - Step definitions implementing the test logic
- `environment.py` - Behave configuration and setup/teardown hooks

## Prerequisites

1. **Install dependencies**:
   ```bash
   uv sync --group dev
   ```

2. **Database setup**:
   Make sure your database is set up and migrations are applied:
   ```bash
   uv run alembic upgrade head
   ```

3. **FastAPI server**:
   The tests require a running FastAPI server. Start it with:
   ```bash
   uv run uvicorn codebase_to_llm.interface.fastapi.app:app --reload --port 8000
   ```

## Running the Tests

### Run all behave tests:
```bash
uv run behave features/
```

### Run specific feature:
```bash
uv run behave features/video_key_insights.feature
```

### Run with verbose output:
```bash
uv run behave features/ --verbose
```

### Run with custom server URL:
```bash
TEST_BASE_URL=http://localhost:8080 uv run behave features/
```

### Run from VSCode:
Use the VSCode Run and Debug panel (Ctrl+Shift+D) and select one of the behave configurations:
- **Run Behave Tests - Video Key Insights**: Run only the video key insights tests
- **Run All Behave Tests**: Run all behave tests with verbose output
- **Run Behave Tests - Dry Run**: Syntax check without executing tests
- **Run Behave Tests - Custom Server**: Run tests against localhost:8080

## Test Configuration

The tests use the following configuration:

- **Default server URL**: `http://localhost:8000`
- **Test user**: `kduigou` with existing credentials
- **Authentication**: Uses JWT tokens via the `/auth/token` endpoint

You can override the server URL by setting the `TEST_BASE_URL` environment variable.

## Test Scenarios

### Scenario: Add, verify, and delete video key insights

This scenario tests the complete lifecycle:

1. **Setup**: Creates a test user and authenticates
2. **Create**: Posts new video key insights with sample data
3. **Verify Creation**: Confirms the insights were created and returns a valid ID
4. **Retrieve**: Gets the insights by ID and verifies the data matches
5. **List**: Confirms the insights appear in the user's list
6. **Delete**: Removes the insights from the database
7. **Verify Deletion**: Confirms the insights can no longer be retrieved (404 error)

## Sample Test Data

The tests use the following sample video key insights:

```json
{
  "title": "Test Video Insights",
  "key_insights": [
    {
      "content": "This is a key insight about the video content",
      "video_url": "https://example.com/video.mp4",
      "begin_timestamp": "00:01:30",
      "end_timestamp": "00:02:45"
    },
    {
      "content": "Another important insight from the video",
      "video_url": "https://example.com/video.mp4",
      "begin_timestamp": "00:05:10",
      "end_timestamp": "00:06:20"
    }
  ]
}
```

## API Endpoints Tested

The tests interact with the following FastAPI endpoints:

- `POST /key-insights/video-key-insights` - Create video key insights
- `GET /key-insights/video-key-insights/{id}` - Get video key insights by ID
- `GET /key-insights/all-video-key-insights` - List all video key insights
- `DELETE /key-insights/video-key-insights/{id}` - Delete video key insights
- `POST /auth/register` - Register test user
- `POST /auth/token` - Authenticate and get access token

## Cleanup

The tests include automatic cleanup in the `after_scenario` hook to ensure that any created video key insights are removed even if a test fails.

## Troubleshooting

1. **Server not running**: Make sure the FastAPI server is running on the expected port
2. **Database issues**: Ensure the database is set up and migrations are applied
3. **Authentication failures**: Check that the user registration and authentication endpoints are working
4. **Port conflicts**: Use `TEST_BASE_URL` to specify a different port if needed

## Extending the Tests

To add more test scenarios:

1. Add new scenarios to `video_key_insights.feature`
2. Implement corresponding step definitions in `steps/video_key_insights_steps.py`
3. Update this README with the new test cases
