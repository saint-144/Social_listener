from datetime import timedelta

def build_email_table(posts, title):

    rows = ""

    for p in posts:

        # Convert UTC to IST (+5:30)
        ist_time = p['posted_at'] + timedelta(hours=5, minutes=30) if p['posted_at'] else "N/A"
        fetched_time = p['fetched_at'] + timedelta(hours=5, minutes=30) if p.get('fetched_at') else "N/A"

        rows += f"""
        <tr>
            <td>{ist_time}</td>
            <td>{fetched_time}</td>
            <td>{p['post_text']}</td>
            <td><a href="{p['post_url']}">View Post</a></td>
        </tr>
        """

    html = f"""
    <html>
    <body>

    <h2>{title}</h2>

    <table border="1" cellspacing="0" cellpadding="8">

        <tr>
            <th>Time (IST)</th>
            <th>Fetched At (IST)</th>
            <th>Post Content</th>
            <th>Link</th>
        </tr>

        {rows}

    </table>

    </body>
    </html>
    """

    return html



def build_combined_email_table(posts, title):

    html = f"""
    <h2>{title}</h2>

    <table border="1" cellpadding="6" cellspacing="0"
    style="border-collapse:collapse;font-family:Arial;width:100%;">

        <tr style="background:#f2f2f2">
            <th>Time (IST)</th>
            <th>Fetched At (IST)</th>
            <th>Post</th>
            <th>Link</th>
            <th>Platform</th>
        </tr>
    """

    for post in posts:

        # Convert UTC to IST (+5:30)
        ist_time = post['posted_at'] + timedelta(hours=5, minutes=30) if post['posted_at'] else "N/A"
        fetched_time = post['fetched_at'] + timedelta(hours=5, minutes=30) if post.get('fetched_at') else "N/A"

        html += f"""
        <tr>
            <td>{ist_time}</td>
            <td>{fetched_time}</td>
            <td>{post['post_text'][:200]}</td>
            <td>
                <a href="{post['post_url']}">View</a>
            </td>
            <td>{post['platform']}</td>
        </tr>
        """

    html += "</table>"

    return html