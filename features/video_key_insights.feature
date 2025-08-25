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
