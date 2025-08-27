Feature: Video Subtitle Management
  As a user
  I want to add French subtitles to a video, update them to be glowing, and burn them into MP4
  So that I can create videos with enhanced subtitle styling

  Background:
    Given the FastAPI server is running
    And I have a valid user account
    And I am authenticated

  Scenario: Get ASS file by video ID
    Given I have a test video file id "a214016d-4e57-4df3-b644-1c3f0288c1e0" on the server
    #When I request to add French subtitles to the video
    #Then I should receive a task ID for subtitle generation
    
    #When I wait for the subtitle generation task to complete
    #Then the subtitle generation task should be completed successfully
    #And I should have both video file ID and subtitle file ID
    
    When I get the ASS file associated to video id "a214016d-4e57-4df3-b644-1c3f0288c1e0"
    Then I should receive the ASS file content
    And the ASS file should be properly formatted
