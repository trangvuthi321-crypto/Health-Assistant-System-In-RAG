-- 健康助手菜单（在已导入 communitypension 库后执行）
USE communitypension;

INSERT INTO mainmenu (id, title, path) VALUES (700, '健康助手', '/assistant');

-- 按现有 submenu 观测到的角色分别授权，保证各角色都能看到入口
INSERT INTO submenu (id, title, path, mid, roleId) VALUES (701, '健康助手', '/assistant', 700, '1');
INSERT INTO submenu (id, title, path, mid, roleId) VALUES (702, '健康助手', '/assistant', 700, '1234');
INSERT INTO submenu (id, title, path, mid, roleId) VALUES (703, '健康助手', '/assistant', 700, '24');
INSERT INTO submenu (id, title, path, mid, roleId) VALUES (704, '健康助手', '/assistant', 700, '12');
INSERT INTO submenu (id, title, path, mid, roleId) VALUES (705, '健康助手', '/assistant', 700, '14');
INSERT INTO submenu (id, title, path, mid, roleId) VALUES (706, '健康助手', '/assistant', 700, '134');
