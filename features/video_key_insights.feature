Feature: Video Key Insights Management
  As a user
  I want to manage video key insights
  So that I can store, retrieve, and delete key insights from videos

  Background:
    Given the FastAPI server is running
    And I have a valid user account
    And I am authenticated

  Scenario: Add, verify, and delete video key insights
    Given I have video key insights data with title "Test Video Insights"
    When I create the video key insights via POST request
    Then the video key insights should be created successfully
    And I should receive a valid video key insights ID
    
    When I retrieve the video key insights by ID
    Then I should get the same video key insights data
    And the title should be "Test Video Insights"
    
    When I list all video key insights
    Then the created video key insights should be in the list
    
    When I delete the video key insights by ID
    Then the video key insights should be deleted successfully
    
    When I try to retrieve the deleted video key insights
    Then I should get a 404 error

  Scenario: Create video key insights from YouTube URL, wait for completion, verify insights, and delete
    Given I have a YouTube video URL "https://youtu.be/2YlYPZt6WCA?si=BB6fzATgVS4KJk4R"
    And I have a model ID "gpt-4o" for key insights processing
    And I have a target language "French"
    And I want 3 key insights
    When I trigger key insights extraction for the YouTube URL
    Then I should receive a task ID for the key insights

    When I wait for the key insights task to complete
    Then the key insights task should be completed successfully
    And the extracted key insights should contain 3 items

    When I create video key insights from the task result
    Then the video key insights should be created successfully
    And I should receive a valid video key insights ID

    When I retrieve the video key insights by ID
    Then I should get the same video key insights data

    When I delete the video key insights by ID
    Then the video key insights should be deleted successfully
