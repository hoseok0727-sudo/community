from app.api.topics import selected_board_briefing


def test_selected_board_briefing_returns_empty_without_boards(db_session):
    response = selected_board_briefing(
        gallery_ids=[],
        window_hours=24,
        limit=20,
        per_gallery_cap=120,
        db=db_session,
    )
    assert response.topic_count == 0
    assert response.topics == []

