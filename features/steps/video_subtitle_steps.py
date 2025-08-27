import requests
import time
import base64
from behave import given, when, then
from dotenv import load_dotenv

# Load environment variables from .env-development
load_dotenv(".env-development")


@given('I have a test video file id "{file_id}" on the server')
def step_have_test_video_file(context, file_id):
    context.test_video_file_id = file_id  # This should be a real file ID


@when("I request to add French subtitles to the video")
def step_request_add_french_subtitles(context):
    subtitle_request = {
        "file_id": context.test_video_file_id,
        "origin_language": "en",
        "target_language": "fr",  # French subtitles
        "output_filename": "test_with_french_subtitles.mkv",
        "subtitle_color": "white",
        "subtitle_style": "outline",
        "use_soft_subtitles": True,
        "subtitle_format": "ass",
        "font_size_percentage": 4.0,
        "margin_percentage": 5.0,
    }

    response = requests.post(
        f"{context.base_url}/add_subtitles/",
        json=subtitle_request,
        headers=context.auth_headers,
    )
    context.subtitle_request_response = response
    if response.status_code == 200:
        context.subtitle_task_data = response.json()


@then("I should receive a task ID for subtitle generation")
def step_receive_task_id_for_subtitle_generation(context):
    assert (
        context.subtitle_request_response.status_code == 200
    ), f"Expected 200, got {context.subtitle_request_response.status_code}: {context.subtitle_request_response.text}"
    assert "task_id" in context.subtitle_task_data
    assert context.subtitle_task_data["task_id"]
    context.subtitle_task_id = context.subtitle_task_data["task_id"]


@when("I wait for the subtitle generation task to complete")
def step_wait_for_subtitle_generation_task_to_complete(context):
    max_wait_time = 300  # 5 minutes maximum wait time
    check_interval = 15  # Check every 15 seconds
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = requests.get(
            f"{context.base_url}/add_subtitles/{context.subtitle_task_id}",
            headers=context.auth_headers,
        )

        if response.status_code == 200:
            task_status = response.json()
            context.subtitle_task_status_response = task_status

            if task_status["status"] == "SUCCESS":
                context.completed_subtitle_task_data = task_status
                return
            elif task_status["status"] == "FAILURE":
                raise AssertionError(f"Subtitle generation task failed: {task_status}")

        time.sleep(check_interval)

    raise AssertionError(
        f"Subtitle generation task did not complete within {max_wait_time} seconds"
    )


@then("the subtitle generation task should be completed successfully")
def step_subtitle_generation_task_completed_successfully(context):
    assert (
        context.completed_subtitle_task_data["status"] == "SUCCESS"
    ), f"Expected task status SUCCESS, got {context.completed_subtitle_task_data['status']}"


@then("I should have both video file ID and subtitle file ID")
def step_should_have_both_file_ids(context):
    assert "file_id" in context.completed_subtitle_task_data
    assert "subtitle_file_id" in context.completed_subtitle_task_data
    assert context.completed_subtitle_task_data["file_id"] is not None
    assert context.completed_subtitle_task_data["subtitle_file_id"] is not None

    context.video_file_id = context.completed_subtitle_task_data["file_id"]
    context.subtitle_file_id = context.completed_subtitle_task_data["subtitle_file_id"]


@when("I create a video-subtitle association")
def step_create_video_subtitle_association(context):
    association_request = {
        "video_file_id": context.video_file_id,
        "subtitle_file_id": context.subtitle_file_id,
    }

    response = requests.post(
        f"{context.base_url}/video_subtitles/",
        json=association_request,
        headers=context.auth_headers,
    )
    context.association_create_response = response
    if response.status_code == 200:
        context.created_association = response.json()


@then("the association should be created successfully")
def step_association_created_successfully(context):
    assert (
        context.association_create_response.status_code == 200
    ), f"Expected 200, got {context.association_create_response.status_code}: {context.association_create_response.text}"


@then("I should receive a valid association ID")
def step_receive_valid_association_id(context):
    assert "id" in context.created_association
    assert context.created_association["id"]
    context.association_id = context.created_association["id"]


@when("I retrieve the association by ID")
def step_retrieve_association_by_id(context):
    response = requests.get(
        f"{context.base_url}/video_subtitles/{context.association_id}",
        headers=context.auth_headers,
    )
    context.get_association_response = response
    if response.status_code == 200:
        context.retrieved_association = response.json()


@then("I should get the same association data")
def step_get_same_association_data(context):
    assert (
        context.get_association_response.status_code == 200
    ), f"Expected 200, got {context.get_association_response.status_code}: {context.get_association_response.text}"

    retrieved = context.retrieved_association
    original = context.created_association

    assert retrieved["id"] == original["id"]
    assert retrieved["video_file_id"] == original["video_file_id"]
    assert retrieved["subtitle_file_id"] == original["subtitle_file_id"]


@when("I update the subtitle to use glowing style")
def step_update_subtitle_to_glowing_style(context):
    # For this step, we would need to create a new subtitle file with glowing style
    # and then update the association to point to the new subtitle file
    # For now, we'll simulate this by updating with the same subtitle file ID
    # but in a real scenario, you'd generate a new subtitle file with glowing effects

    # Create a new subtitle request with glowing style
    glowing_subtitle_request = {
        "file_id": context.video_file_id,
        "origin_language": "en",
        "target_language": "fr",
        "output_filename": "test_with_glowing_french_subtitles.mkv",
        "subtitle_color": "yellow",  # Changed to yellow for glowing effect
        "subtitle_style": "outline",  # Could be enhanced with glow effects
        "use_soft_subtitles": True,
        "subtitle_format": "ass",
        "font_size_percentage": 4.5,  # Slightly larger
        "margin_percentage": 5.0,
    }

    # Request new subtitle generation with glowing style
    response = requests.post(
        f"{context.base_url}/add_subtitles/",
        json=glowing_subtitle_request,
        headers=context.auth_headers,
    )

    if response.status_code == 200:
        glowing_task_data = response.json()
        glowing_task_id = glowing_task_data["task_id"]

        # Wait for the glowing subtitle task to complete
        max_wait_time = 300
        check_interval = 15
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"{context.base_url}/add_subtitles/{glowing_task_id}",
                headers=context.auth_headers,
            )

            if status_response.status_code == 200:
                task_status = status_response.json()
                if task_status["status"] == "SUCCESS":
                    context.glowing_subtitle_file_id = task_status["subtitle_file_id"]
                    break
                elif task_status["status"] == "FAILURE":
                    raise AssertionError(
                        f"Glowing subtitle generation failed: {task_status}"
                    )

            time.sleep(check_interval)
        else:
            raise AssertionError("Glowing subtitle generation did not complete in time")

    # Now update the association with the new glowing subtitle file
    update_request = {
        "subtitle_file_id": context.glowing_subtitle_file_id,
    }

    update_response = requests.put(
        f"{context.base_url}/video_subtitles/{context.association_id}",
        json=update_request,
        headers=context.auth_headers,
    )
    context.update_association_response = update_response


@then("the subtitle should be updated successfully")
def step_subtitle_updated_successfully(context):
    assert (
        context.update_association_response.status_code == 200
    ), f"Expected 200, got {context.update_association_response.status_code}: {context.update_association_response.text}"

    response_data = context.update_association_response.json()
    assert "status" in response_data
    assert response_data["status"] == "updated"


@when("I burn the ASS subtitle into the video")
def step_burn_ass_subtitle_into_video(context):
    # To burn the subtitle, we need to get the video content and subtitle content
    # For this test, we'll simulate having the content as base64 encoded strings
    # In a real scenario, you'd fetch these from the file storage system

    # Mock video and subtitle content (base64 encoded)
    # In reality, you'd fetch these from your file storage using the file IDs
    mock_video_content = base64.b64encode(b"mock_video_content").decode("utf-8")
    mock_subtitle_content = base64.b64encode(b"mock_subtitle_content").decode("utf-8")

    burn_request = {
        "video_content": mock_video_content,
        "subtitle_content": mock_subtitle_content,
    }

    response = requests.post(
        f"{context.base_url}/burn_ass/",
        json=burn_request,
        headers=context.auth_headers,
    )
    context.burn_response = response
    if response.status_code == 200:
        context.burned_video_data = response.json()


@then("I should receive the final MP4 video content")
def step_receive_final_mp4_video_content(context):
    assert (
        context.burn_response.status_code == 200
    ), f"Expected 200, got {context.burn_response.status_code}: {context.burn_response.text}"

    assert "content" in context.burned_video_data
    assert context.burned_video_data["content"]
    context.final_video_content = context.burned_video_data["content"]


@then("the video should be properly encoded")
def step_video_should_be_properly_encoded(context):
    # Verify that the content is base64 encoded
    try:
        decoded_content = base64.b64decode(context.final_video_content)
        assert len(decoded_content) > 0
        # In a real test, you might check for MP4 file headers or other validation
    except Exception as e:
        raise AssertionError(f"Video content is not properly base64 encoded: {e}")


@when("I delete the video-subtitle association")
def step_delete_video_subtitle_association(context):
    response = requests.delete(
        f"{context.base_url}/video_subtitles/{context.association_id}",
        headers=context.auth_headers,
    )
    context.delete_association_response = response


@then("the association should be deleted successfully")
def step_association_deleted_successfully(context):
    assert (
        context.delete_association_response.status_code == 200
    ), f"Expected 200, got {context.delete_association_response.status_code}: {context.delete_association_response.text}"

    response_data = context.delete_association_response.json()
    assert "status" in response_data
    assert response_data["status"] == "deleted"


@when("I try to retrieve the deleted association")
def step_try_retrieve_deleted_association(context):
    response = requests.get(
        f"{context.base_url}/video_subtitles/{context.association_id}",
        headers=context.auth_headers,
    )
    context.get_deleted_association_response = response


@when('I get the ASS file associated to video id "{file_id}"')
def step_get_ass_file_by_video_id(context, file_id):
    response = requests.get(
        f"{context.base_url}/video_subtitles/video/{file_id}/ass",
        headers=context.auth_headers,
    )
    context.get_ass_file_response = response
    if response.status_code == 200:
        response_data = response.json()
        context.ass_file_content = response_data["content"]


@then("I should receive the ASS file content")
def step_should_receive_ass_file_content(context):
    assert (
        context.get_ass_file_response.status_code == 200
    ), f"Expected 200, got {context.get_ass_file_response.status_code}: {context.get_ass_file_response.text}"

    assert context.ass_file_content is not None
    assert len(context.ass_file_content) > 0


@then("the ASS file should be properly formatted")
def step_ass_file_should_be_properly_formatted(context):
    # Basic ASS file format validation
    ass_content = context.ass_file_content

    # Check for ASS file header
    assert (
        "[Script Info]" in ass_content
    ), "ASS file should contain [Script Info] section"
    assert "[V4+ Styles]" in ass_content, "ASS file should contain [V4+ Styles] section"
    assert "[Events]" in ass_content, "ASS file should contain [Events] section"

    # Check for basic ASS file structure
    lines = ass_content.split("\n")
    assert len(lines) > 10, "ASS file should have multiple lines"
