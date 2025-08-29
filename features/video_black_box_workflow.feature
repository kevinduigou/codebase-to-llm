Feature: Complete Video Processing Black Box Workflow
  As a user
  I want to upload a video, add subtitles, burn them into the video, and download the final result
  So that I can process videos end-to-end through the API

  Background:
    Given the FastAPI server is running
    And I have a valid user account
    And I am authenticated

  Scenario: Complete black box video processing workflow
    Given I have a test video file "features/inputs/video.mkv"
    When I upload the video file via POST "/files/upload-from-desktop"
    Then I should receive a file ID for the uploaded video
    
    When I request to add subtitles via POST "/add_subtitles/"
    Then I should receive a task ID for subtitle generation
    
    When I wait for the subtitle generation task to complete
    Then the subtitle generation task should be completed successfully
    And I should have the video file ID with subtitles
    
    When I get the subtitle content via GET "/video_subtitles/video/{video_file_id}/ass"
    Then I should receive the subtitle file content

    When I transform the subtitle content via POST "/video_subtitles/video/{video_file_id}/magic_ass"
    Then I should receive the transformed subtitle content

    When I update the subtitle content with the transformed content via PUT "/video_subtitles/video/{video_file_id}/ass"
    Then the subtitle content should be updated successfully
    
    When I request to burn ASS subtitles via POST "/burn_ass/video/{video_file_id}"
    Then I should receive a task ID for burning subtitles
    
    When I wait for the burn task to complete via GET "/burn_ass/{task_id}"
    Then the burn task should be completed successfully
    And I should have the final video file ID
    
    When I download the final video via GET "/files/{file_id}/download"
    Then I should receive the processed video file
    And the video file should be properly formatted
    
    When I delete the final video via DELETE "/files/{file_id}"
    Then the video file should be deleted successfully
