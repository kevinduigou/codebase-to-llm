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

    When I try to retrieve the deleted video summary
    Then I should get a 404 error
