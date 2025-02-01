INSERT INTO user (username, password)
VALUES
  ('test', 'scrypt:32768:8:1$zptujoyVuiYJmu0L$12d86c1ec80ad019a73144829a9dbc2c7665c1197a10b22b7820c65e1e5af45308b75a23aabb3812ae72d5e14b2627865eda52acffc97b63825799de6ce56e5c'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO post (title, body, author_id, created)
VALUES
  ('test title', 'test-body', 1, '2018-01-01 00:00:00');