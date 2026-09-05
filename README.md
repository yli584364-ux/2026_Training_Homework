# 2026_Training_Homework
2026 培训作业：通过 Pull Request 提交代码，通过 GitHub Actions 查看测试结果。

## 第一次作业：电机速度限幅（C 语言，约 5～10 分钟）

实现函数 `int clamp_speed(int target_speed)`，将目标速度限制在 **[-1000, 1000]**：

- 大于 1000，返回 1000。
- 小于 -1000，返回 -1000。
- 其余情况返回原值，包含两个边界。

本题只需要 `if` 和 `return`，不需要单片机、PID、循环或指针。输入范围是 C 的 `int` 可表示范围；代码在 GitHub 的普通 Linux 电脑上运行。

| 函数调用 | 应返回 |
| --- | ---: |
| `clamp_speed(1500)` | 1000 |
| `clamp_speed(-1500)` | -1000 |
| `clamp_speed(300)` | 300 |
| `clamp_speed(0)` | 0 |
| `clamp_speed(1000)` | 1000 |
| `clamp_speed(-1000)` | -1000 |

复制 [函数模板](assignments/01_clamp_speed/template.c)，补全函数体。**不要编写 `main()`、`scanf()` 或 `printf()`**；测试程序会直接调用你的函数，并比较返回值。

## 提交步骤

1. Fork 本仓库到自己的 GitHub 账号，再克隆自己的 Fork。已有写权限的队员也可以在本仓库创建个人分支。
2. 创建分支，例如 `homework/01-clamp-speed`。
3. 新建文件 `submissions/你的GitHub用户名/clamp_speed.c`，复制模板并完成题目。目录名必须与 PR 作者的 GitHub 用户名一致（大小写不敏感），例如 `submissions/octocat/clamp_speed.c`。
4. 本次作业只提交自己的这一个 `.c` 文件；不修改测试、题目、工作流或其他人的代码。
5. 提交并推送，然后向 **HITSZ-WTRobot/2026_Training_Homework 的 main** 发起 Pull Request。

以下命令以用户名 `octocat` 为例，请替换为你自己的用户名。在 Git Bash / Linux / macOS 终端运行：

```bash
git clone https://github.com/octocat/2026_Training_Homework.git
cd 2026_Training_Homework
git switch -c homework/01-clamp-speed
mkdir -p submissions/octocat
cp assignments/01_clamp_speed/template.c submissions/octocat/clamp_speed.c
# 在编辑器中完成函数，再继续下面的命令
git diff
git add submissions/octocat/clamp_speed.c
git commit -m "feat: 完成电机速度限幅作业"
git push -u origin homework/01-clamp-speed
```

PR 标题示例：`homework: 张三完成速度限幅`。正文说明实现思路和测试结果。进入 PR 的 **Checks → C homework / grade** 查看日志；出现红叉后，在同一分支修正并再次 push，即可重新测试，无需新建 PR。

第一次从 Fork 提交时，GitHub 可能需要维护者点击 **Approve and run workflows**；等待批准不代表代码错误。

## 测试与验收

自动检查依次验证提交路径、C11 编译、程序运行和返回值：

- 编译参数：`-std=c11 -Wall -Wextra -Werror -pedantic`。
- 测试 15 个明确样例（含 `INT_MIN`、`INT_MAX`），以及 -2000 到 2000 的全部整数，共 **4016 次调用**。
- 错误答案会显示输入、预期值和实际值；编译错误、崩溃、超时均失败。
- 每份程序最多运行 3 秒。每个 PR 只评测本次修改的个人作业，互不干扰。
- 通过自动测试后，还需学长/学姐检查命名、可读性及修改范围，再决定是否合并。

本地有 Python 3.10+ 和 GCC 时，可运行与 Actions 相同的判题脚本：

```bash
python scripts/check_homework.py submissions/octocat/clamp_speed.c
```

只想使用 C 编译器，也可以运行：

```bash
gcc -std=c11 -Wall -Wextra -Werror -pedantic submissions/octocat/clamp_speed.c tests/test_clamp_speed.c -o clamp_test
./clamp_test
```

模板尚未完成时测试失败是正常的。Windows 的编译结果通常为 `clamp_test.exe`；可用 Clang 时，判题脚本支持 `--cc clang`。

## 教师配置与维护

[GitHub Actions 工作流](.github/workflows/c-homework.yml) 在面向 `main` 的 PR 创建、更新、重开时触发；合入 `main` 后重新检查全部已提交作业，也支持手动运行。

首次使用时，将这套题目及工作流合入 `main`，并确保仓库 Actions 已启用。整个过程不需要配置 Secret，也不需要自托管 Runner。学员应从包含这套文件的版本 Fork。

建议在仓库的分支保护或 Ruleset 中要求 `C homework / grade` 检查成功并完成 Review 后才能合并；本配置文件本身不会自动修改仓库保护设置。

题目、测试和工作流的维护 PR 可以单独修改教学基础文件，并执行判题器自检；维护 PR 不会被当成学员作业。禁止将维护改动和作业答案混在一个 PR。这是用于教学的公开测试，**不是防作弊沙箱**；Review 仍需确认学员未修改判题规则。仅使用 GitHub 托管的临时 Runner 和 `pull_request` 事件，不将学员代码放进有写权限或 Secrets 的 `pull_request_target` 任务。

维护者本地检查：

```bash
python -m unittest discover -s tests -p "test_grader.py" -v
python scripts/check_homework.py --all
```

尚无学员文件时，维护检查会明确显示“没有学员作业”，只表示基础配置自检成功。

参考：[GitHub PR 触发规则](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)、[Fork 工作流审批](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)。
