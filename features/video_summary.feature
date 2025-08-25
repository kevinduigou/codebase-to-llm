Feature: Video Summary Management
  As a user
  I want to manage video summaries
  So that I can store, retrieve, and delete summaries of videos

  Background:
    Given the FastAPI server is running
    And I have a valid user account
    And I am authenticated

  Scenario: Add, verify, and delete video summary
    Given I have video summary data with title "Test Video Summary"
    When I create the video summary via POST request
    Then the video summary should be created successfully
    And I should receive a valid video summary ID

    When I retrieve the video summary by ID
    Then I should get the same video summary data
    And the summary title should be "Test Video Summary"

    When I list all video summaries
    Then the created video summary should be in the list

    When I delete the video summary by ID
    Then the video summary should be deleted successfully
    
    # Cleanup test data
    When I cleanup the test model and API key
    Then the test data should be cleaned up successfully

    When I try to retrieve the deleted video summary
    Then I should get a 404 error

  Scenario: Create video summary from YouTube URL, wait for completion, verify segments, and delete
    Given I have a YouTube video URL "https://youtu.be/2YlYPZt6WCA?si=BB6fzATgVS4KJk4R"
    And I have a model ID "gpt-4o" for video processing
    And I have a target language "French"
    When I trigger video summary creation for the YouTube URL
    Then I should receive a task ID for the video summary

    When I wait for the video summary task to complete
    Then the video summary task should be completed successfully
    And the video summary should contain multiple segments

    When I create a video summary from the task result
    Then the video summary should be created successfully
    And I should receive a valid video summary ID

    When I retrieve the video summary by ID
    Then I should get the video summary data
    And the video summary should have different segments with timestamps

    When I delete the video summary by ID
    Then the video summary should be deleted successfully

  Scenario: Create video summary from YouTube URL with Anthropic, wait for completion, verify segments, and delete
    Given I have a YouTube video URL "https://youtu.be/2YlYPZt6WCA?si=BB6fzATgVS4KJk4R"
    And I have a model ID "claude-sonnet-4-20250514" for video processing
    And I have a target language "French"
    When I trigger video summary creation for the YouTube URL
    Then I should receive a task ID for the video summary

    When I wait for the video summary task to complete
    Then the video summary task should be completed successfully
    And the video summary should contain multiple segments

    When I create a video summary from the task result
    Then the video summary should be created successfully
    And I should receive a valid video summary ID

    When I retrieve the video summary by ID
    Then I should get the video summary data
    And the video summary should have different segments with timestamps

    When I delete the video summary by ID
    Then the video summary should be deleted successfully