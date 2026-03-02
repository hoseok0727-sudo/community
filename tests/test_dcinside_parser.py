from app.collectors.dcinside import parse_dcinside_list


def test_parse_dcinside_list_basic():
    html = """
    <table>
      <tr class="ub-content us-post" data-no="12345">
        <td class="gall_num">12345</td>
        <td class="gall_tit ub-word">
          <a href="/board/view/?id=test&no=12345">테스트 떡밥 제목</a>
          <span class="reply_num">[7]</span>
        </td>
        <td class="gall_writer" data-nick="tester">tester</td>
        <td class="gall_date" title="2026-03-02 19:10:00">19:10</td>
        <td class="gall_count">1,234</td>
        <td class="gall_recommend">56</td>
      </tr>
    </table>
    """
    posts = parse_dcinside_list(html, source_key="test")
    assert len(posts) == 1
    post = posts[0]
    assert post.external_id == "12345"
    assert post.title == "테스트 떡밥 제목"
    assert post.comment_count == 7
    assert post.view_count == 1234
    assert post.upvote_count == 56
    assert "board/view" in post.url

