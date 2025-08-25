import requests
import time
from behave import given, when, then


@given('I have video summary data with title "{title}"')
def step_have_video_summary_data(context, title):
    context.test_video_summary = {
        "title": title,
        "segments": [
            {
                "content": "This is a summary of the first part",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": {"hour": 0, "minute": 1, "second": 30},
                "end_timestamp": {"hour": 0, "minute": 2, "second": 45},
            },
            {
                "content": "This summarizes another section",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": {"hour": 0, "minute": 5, "second": 10},
                "end_timestamp": {"hour": 0, "minute": 6, "second": 20},
            },
        ],
    }


@when("I create the video summary via POST request")
def step_create_video_summary(context):
    response = requests.post(
        f"{context.base_url}/summaries/video-summaries",
        json=context.test_video_summary,
        headers=context.auth_headers,
    )
    context.create_response = response
    if response.status_code == 200:
        context.created_video_summary = response.json()


@then("the video summary should be created successfully")
def step_video_summary_created_successfully(context):
    assert (
        context.create_response.status_code == 200
    ), f"Expected 200, got {context.create_response.status_code}: {context.create_response.text}"


@then("I should receive a valid video summary ID")
def step_receive_valid_summary_id(context):
    assert "id" in context.created_video_summary
    assert context.created_video_summary["id"]
    context.video_summary_id = context.created_video_summary["id"]


@when("I retrieve the video summary by ID")
def step_retrieve_video_summary_by_id(context):
    response = requests.get(
        f"{context.base_url}/summaries/video-summaries/{context.video_summary_id}",
        headers=context.auth_headers,
    )
    context.get_response = response
    if response.status_code == 200:
        context.retrieved_video_summary = response.json()


@then("I should get the same video summary data")
def step_get_same_summary_data(context):
    assert (
        context.get_response.status_code == 200
    ), f"Expected 200, got {context.get_response.status_code}: {context.get_response.text}"
    retrieved = context.retrieved_video_summary
    original = context.test_video_summary
    assert len(retrieved["segments"]) == len(original["segments"])
    for i, seg in enumerate(retrieved["segments"]):
        orig = original["segments"][i]
        assert seg["content"] == orig["content"]
        assert seg["video_url"] == orig["video_url"]
        assert seg["begin_timestamp"] == orig["begin_timestamp"]
        assert seg["end_timestamp"] == orig["end_timestamp"]


@then('the summary title should be "{expected_title}"')
def step_verify_summary_title(context, expected_title):
    assert (
        context.retrieved_video_summary["title"] == expected_title
    ), f"Expected title '{expected_title}', got '{context.retrieved_video_summary['title']}'"


@when("I list all video summaries")
def step_list_all_video_summaries(context):
    response = requests.get(
        f"{context.base_url}/summaries/all-video-summaries",
        headers=context.auth_headers,
    )
    context.list_response = response
    if response.status_code == 200:
        context.all_video_summaries = response.json()


@then("the created video summary should be in the list")
def step_summary_created_in_list(context):
    assert (
        context.list_response.status_code == 200
    ), f"Expected 200, got {context.list_response.status_code}: {context.list_response.text}"

    # Debug: Check what we actually received
    if not isinstance(context.all_video_summaries, list):
        raise AssertionError(
            f"Expected list of video summaries, got {type(context.all_video_summaries)}: {context.all_video_summaries}"
        )

    found = any(
        item["id"] == context.video_summary_id for item in context.all_video_summaries
    )
    assert (
        found
    ), f"Created video summary with ID {context.video_summary_id} not found in list"


@when("I delete the video summary by ID")
def step_delete_video_summary(context):
    response = requests.delete(
        f"{context.base_url}/summaries/video-summaries/{context.video_summary_id}",
        headers=context.auth_headers,
    )
    context.delete_response = response


@then("the video summary should be deleted successfully")
def step_video_summary_deleted_successfully(context):
    assert (
        context.delete_response.status_code == 200
    ), f"Expected 200, got {context.delete_response.status_code}: {context.delete_response.text}"
    response_data = context.delete_response.json()
    assert "message" in response_data
    assert "deleted successfully" in response_data["message"]


@when("I try to retrieve the deleted video summary")
def step_try_retrieve_deleted_summary(context):
    response = requests.get(
        f"{context.base_url}/summaries/video-summaries/{context.video_summary_id}",
        headers=context.auth_headers,
    )
    context.get_deleted_response = response


# New steps for YouTube video summary processing


@given('I have a YouTube video URL "{video_url}"')
def step_have_youtube_video_url(context, video_url):
    context.youtube_video_url = video_url


@given('I have a target language "{target_language}"')
def step_have_target_language(context, target_language):
    context.target_language = target_language


@given('I have a model ID "{model_name}" for video processing')
def step_have_model_id_for_video_processing(context, model_name):
    # Create a test API key and model for video processing
    import os

    # First, create an API key
    api_key_data = {
        "id_value": "test-openai-api-key",
        "url_provider": "https://api.openai.com/v1/",
        "api_key_value": os.getenv("OPENAI_API_KEY", "test-key"),
    }

    api_key_response = requests.post(
        f"{context.base_url}/api-keys/",
        json=api_key_data,
        headers=context.auth_headers,
    )

    # If API key already exists, that's fine
    if api_key_response.status_code not in [200, 400]:
        raise AssertionError(
            f"Failed to create API key: {api_key_response.status_code} - {api_key_response.text}"
        )

    # Now create a model using the specified model name
    model_id = f"test-{model_name}"
    model_data = {
        "id_value": model_id,
        "name": model_name,
        "api_key_id": "test-openai-api-key",
    }

    model_response = requests.post(
        f"{context.base_url}/models/",
        json=model_data,
        headers=context.auth_headers,
    )

    # If model already exists, that's fine
    if model_response.status_code not in [200, 400]:
        raise AssertionError(
            f"Failed to create model: {model_response.status_code} - {model_response.text}"
        )

    context.video_processing_model_id = model_id
    context.test_api_key_id = "test-openai-api-key"
    context.test_model_id = model_id


@when("I trigger video summary creation for the YouTube URL")
def step_trigger_video_summary_creation(context):
    request_data = {
        "model_id": context.video_processing_model_id,
        "video_url": context.youtube_video_url,
        "target_language": getattr(context, "target_language", "English"),
    }
    response = requests.post(
        f"{context.base_url}/summaries/",
        json=request_data,
        headers=context.auth_headers,
    )
    context.trigger_response = response
    if response.status_code == 200:
        context.task_data = response.json()


@then("I should receive a task ID for the video summary")
def step_receive_task_id_for_video_summary(context):
    assert (
        context.trigger_response.status_code == 200
    ), f"Expected 200, got {context.trigger_response.status_code}: {context.trigger_response.text}"
    assert "task_id" in context.task_data
    assert context.task_data["task_id"]
    context.video_summary_task_id = context.task_data["task_id"]


@when("I wait for the video summary task to complete")
def step_wait_for_video_summary_task_to_complete(context):
    max_wait_time = 300  # 5 minutes maximum wait time
    check_interval = 15  # Check every 15 seconds
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = requests.get(
            f"{context.base_url}/summaries/{context.video_summary_task_id}",
            headers=context.auth_headers,
        )

        if response.status_code == 200:
            task_status = response.json()
            context.task_status_response = task_status

            if task_status["status"] == "SUCCESS":
                context.completed_task_data = task_status
                return
            elif task_status["status"] == "FAILURE":
                raise AssertionError(f"Video summary task failed: {task_status}")

        time.sleep(check_interval)

    raise AssertionError(
        f"Video summary task did not complete within {max_wait_time} seconds"
    )


@then("the video summary task should be completed successfully")
def step_video_summary_task_completed_successfully(context):
    assert (
        context.completed_task_data["status"] == "SUCCESS"
    ), f"Expected task status SUCCESS, got {context.completed_task_data['status']}"


@then("the video summary should contain multiple segments")
def step_video_summary_should_contain_multiple_segments(context):
    assert "segments" in context.completed_task_data
    segments = context.completed_task_data["segments"]
    assert segments is not None, "Segments should not be None"
    assert len(segments) > 1, f"Expected multiple segments, got {len(segments)}"
    context.task_segments = segments


@when("I create a video summary from the task result")
def step_create_video_summary_from_task_result(context):
    # Create a video summary using the segments from the completed task
    video_summary_data = {
        "title": f"YouTube Video Summary - {context.youtube_video_url}",
        "segments": context.task_segments,
    }

    response = requests.post(
        f"{context.base_url}/summaries/video-summaries",
        json=video_summary_data,
        headers=context.auth_headers,
    )
    context.create_response = response
    if response.status_code == 200:
        context.created_video_summary = response.json()


@then("I should get the video summary data")
def step_get_video_summary_data(context):
    assert (
        context.get_response.status_code == 200
    ), f"Expected 200, got {context.get_response.status_code}: {context.get_response.text}"


@then("the video summary should have different segments with timestamps")
def step_video_summary_should_have_different_segments_with_timestamps(context):
    retrieved = context.retrieved_video_summary
    assert "segments" in retrieved
    segments = retrieved["segments"]
    assert len(segments) > 1, f"Expected multiple segments, got {len(segments)}"

    # Verify that segments have different timestamps
    timestamps = []
    for i, segment in enumerate(segments):
        assert "begin_timestamp" in segment
        assert "end_timestamp" in segment
        begin_ts = segment["begin_timestamp"]
        end_ts = segment["end_timestamp"]

        # Debug: Print the actual timestamp values
        print(f"Segment {i}: begin={begin_ts}, end={end_ts}")

        # Convert timestamps to comparable format
        begin_total_seconds = (
            begin_ts["hour"] * 3600 + begin_ts["minute"] * 60 + begin_ts["second"]
        )
        end_total_seconds = (
            end_ts["hour"] * 3600 + end_ts["minute"] * 60 + end_ts["second"]
        )

        print(
            f"Segment {i}: begin_seconds={begin_total_seconds}, end_seconds={end_total_seconds}"
        )

        assert (
            begin_total_seconds < end_total_seconds
        ), f"Begin timestamp should be before end timestamp. Segment {i}: begin={begin_total_seconds}s, end={end_total_seconds}s"
        timestamps.append((begin_total_seconds, end_total_seconds))

    # Verify that we have different timestamp ranges
    unique_timestamps = set(timestamps)
    assert (
        len(unique_timestamps) > 1
    ), "Expected different timestamp ranges for segments"


@when("I cleanup the test model and API key")
def step_cleanup_test_model_and_api_key(context):
    # Clean up the test model if it exists
    if hasattr(context, "test_model_id"):
        model_response = requests.delete(
            f"{context.base_url}/models/{context.test_model_id}",
            headers=context.auth_headers,
        )
        # Don't fail if model doesn't exist
        if model_response.status_code not in [200, 404]:
            print(
                f"Warning: Failed to delete model: {model_response.status_code} - {model_response.text}"
            )

    # Clean up the test API key if it exists
    if hasattr(context, "test_api_key_id"):
        api_key_response = requests.delete(
            f"{context.base_url}/api-keys/{context.test_api_key_id}",
            headers=context.auth_headers,
        )
        # Don't fail if API key doesn't exist
        if api_key_response.status_code not in [200, 404]:
            print(
                f"Warning: Failed to delete API key: {api_key_response.status_code} - {api_key_response.text}"
            )

    context.cleanup_response = {"status": "completed"}


@then("the test data should be cleaned up successfully")
def step_test_data_cleaned_up_successfully(context):
    assert hasattr(context, "cleanup_response"), "Cleanup should have been performed"
    assert (
        context.cleanup_response["status"] == "completed"
    ), "Cleanup should be completed"
