/**
 * Homepage translations — EN + ZH
 *
 * Loaded after i18n.js on the homepage.
 * Calls i18n.init() with all translation strings.
 */

i18n.init({
    en: {
        nav: {
            brandText: 'Psylens.AI',
            features: 'Features',
            home: 'Home',
            docs: 'Documentation',
            overview: 'Overview',
            syntax: 'Syntax Reference',
            execution: 'Execution Model',
            compilation: 'Compilation',
            examples: 'Examples',
            demo: 'Demo',
            about: 'About'
        },
        hero: {
            title: 'The working language for AI agents',
            subtitle: 'NormCode lets you break down and constrain AI agent behavior — step by step, in readable, structured syntax. Build agent workflows that are truly your own.',
            downloadBtn: 'Download Canvas',
            paperBtn: 'Paper',
            youSay: 'You say this',
            instructionLabel: 'Instruction',
            instructionText: 'Read the uploaded file and create a report. Then summarize the findings using the report and a style guide.',
            itCompiles: 'It compiles to',
            itBecomes: 'It runs step by step'
        },
        gap: {
            title: 'Understand what your AI agent actually does',
            raw: {
                title: 'Raw AI Models',
                text: 'Claude, GPT, etc. Each model is trained on specific ways of working. You learn its patterns, its quirks, its prompt style.',
                verdict: 'You adapt to how it works.'
            },
            frameworks: {
                title: 'Agent Code Frameworks',
                text: 'LangChain, LlamaIndex, CrewAI. Python code — only the dev can read it. Only the dev can change it.',
                verdict: 'You need coding expertise to maintain it.'
            },
            nocode: {
                title: 'Workflow Orchestration UI',
                text: 'Dify, Coze, etc. Drag-and-drop locked UIs. Requires carefully crafting workflows for each specific use case.',
                verdict: 'Not suited for complex scenarios.'
            },
            punchline: 'NormCode gives you control — through plans that combine minimal formalization with natural language. No coding required. Easily read and run. AI can generate them. Scale, combine, reuse.'
        },
        // language: → loaded from lang/language-section.js
        whyLang: {
            title: 'Only a language can be learnt',
            subtitle: 'Tools are used. Platforms are subscribed to. A language becomes how you think.',
            learn: {
                title: 'Learn it once, describe any workflow',
                text: 'Like SQL for databases — learn NormCode and you can describe any AI agent workflow. Not tied to any specific framework, model, or platform.'
            },
            debug: {
                title: 'Every step is debuggable on its own',
                text: 'No global context means each step has a known, bounded set of inputs. Debug one step in isolation. When something goes wrong, check the inputs — they\'re right there in the indentation.'
            },
            artifact: {
                title: 'The plan is YOUR artifact',
                text: 'A .ncds file is a portable text document. Version-control it in Git. Share it with your team. Take it to any orchestrator. No vendor lock-in.'
            }
        },
        lifecycle: {
            title: 'Describe → Compile → Review → Run → Modify → Deploy',
            step1: { title: 'Describe', text: 'Write the plan — or have AI generate it from a description' },
            step2: { title: 'Compile', text: 'The compiler transforms it into an executable workflow.' },
            step3: { title: 'Review', text: 'Read every step before it runs. A manager can approve it.' },
            step4: { title: 'Run', text: 'The orchestrator runs each step. Every input/output is recorded.' },
            step5: { title: 'Modify', text: 'Change one step without breaking others. Fork from any checkpoint.' },
            step6: { title: 'Deploy', text: 'Ship it. The file is yours — git it, publish it, hand it to a colleague.' }
        },
        seeIt: {
            title: 'From plan to output — watch a real agent run',
            subtitle: 'See NormCode Canvas in action, or try a live AI agent yourself.',
            videoLabel: 'Canvas Demo',
            clickToPlay: 'Click to play demo',
            videoCaption: 'Design, debug, and run NormCode plans visually',
            demoTitle: 'Live Demo — PPT Agent',
            demoText: 'A real AI agent orchestrated by a NormCode plan. Give it a topic → it produces a full presentation.',
            tryIt: 'Try it yourself →'
        },
        properties: {
            title: 'Built for real complexity',
            subtitle: 'Technical depth for those who want it — here\'s what\'s under the hood.',
            semantic: { title: 'Semantic vs. Syntactic', text: 'Only reasoning costs tokens. Data routing, filtering, and looping are always free.' },
            parallel: { title: 'Parallel Execution', text: 'Independent steps run simultaneously. No manual threading needed.' },
            checkpoint: { title: 'Checkpoint & Resume', text: 'SQLite state at every step. Pause, resume, fork from anywhere.' },
            patching: { title: 'Smart Patching', text: 'Change one step, re-run only what\'s affected. Cache the rest.' },
            flowIndex: { title: 'Flow Index System', text: 'Every node has a unique address. Set breakpoints, trace logs, debug precisely.' },
            compilation: { title: 'Progressive Compilation', text: '4 phases from description to execution. Inspect every stage.' }
        },
        who: {
            title: 'One ecosystem. Every role covered.',
            subtitle: 'Six products, three roles — each built for the people who need it most.',
            designer: {
                tab: 'Agent Designer',
                hint: 'Engineers & Developers',
                title: 'Build the intelligence',
                desc: 'Design agent workflows in NormCode, compile them into executable plans, and deploy autonomous AI agents.',
                lang_desc: 'Define the workflow framework using structured, readable syntax.',
                comp_desc: 'Turn plans into executable workflows through 4 compilation phases.',
                agent_desc: 'The execution unit — runs the compiled workflow step by step.'
            },
            operator: {
                tab: 'Product Operator',
                hint: 'Managers & Ops Teams',
                title: 'Manage & maintain',
                desc: 'Inspect every step, debug with full audit trails, manage versions, and keep the shared workspace running.',
                canvas_desc: 'Visual debugging, step-by-step inspection, and complete audit trails.',
                server_desc: 'Version control, shared workspace, and team collaboration hub.'
            },
            enduser: {
                tab: 'End User',
                hint: 'Domain Experts & Consumers',
                title: 'Use the result',
                desc: 'Interact with AI agents through purpose-built interfaces — no technical knowledge required.',
                clients_desc: 'Purpose-built interfaces for each scenario — chat, forms, dashboards, whatever the workflow needs.'
            },
            language: { name: 'Language' },
            compiler: { name: 'Compiler' },
            agent:    { name: 'Agent' },
            canvas:   { name: 'Canvas' },
            server:   { name: 'Server' },
            clients:  { name: 'Clients' }
        },
        getStarted: {
            title: 'Start here',
            see: {
                title: 'See it first',
                desc: 'I want to understand before I commit.',
                link1: 'Try the live PPT agent'
            },
            learn: {
                title: 'Learn the language',
                desc: 'I want to learn how it works.',
                link1: 'Read the syntax (3 symbols)',
                link2: 'Browse examples',
                link3: 'Understand compilation'
            },
            build: {
                title: 'Build something',
                desc: 'I\'m ready to try it.',
                link1: 'Download Canvas',
                link2: 'Open an example project',
                link3: 'Read the docs'
            }
        },
        footer: {
            tagline: 'The Working Language for AI Agents',
            paper: 'Research Paper',
            contact: 'Contact',
            office: 'TIMETABLE GBA Youth Innovation Base, Nansha, Guangzhou'
        }
    },
    zh: {
        nav: {
            brandText: '心镜智',
            features: '核心功能',
            home: '首页',
            docs: '文档',
            overview: '概述',
            syntax: '语法参考',
            execution: '执行模型',
            compilation: '编译流程',
            examples: '示例',
            demo: '演示',
            about: '关于'
        },
        hero: {
            title: 'AI智能体的工作语言',
            subtitle: 'NormCode（诺码）让您用可读的、结构化的语法，逐步分解约束AI智能体的行为逻辑，构造专属的AI智能体工作方式。',
            downloadBtn: '下载 Canvas',
            paperBtn: '论文',
            youSay: '你这样说',
            instructionLabel: '指令',
            instructionText: '读取上传的文件并创建报告。然后使用报告和风格指南总结发现。',
            itCompiles: '它编译为',
            itBecomes: '它逐步执行'
        },
        gap: {
            title: '读懂你的AI智能体实际在做什么',
            raw: {
                title: '原生AI模型',
                text: 'Claude、千问等。每个模型都有特定的工作方式。你去学习它的模式、它的习惯、它的提示风格。',
                verdict: '你适应它的工作方式。'
            },
            frameworks: {
                title: '智能体代码框架',
                text: 'LangChain、LlamaIndex、CrewAI。Python代码——只有开发者能读懂。只有开发者能修改。',
                verdict: '你需要编程专业知识来维护它。'
            },
            nocode: {
                title: '工作流编排界面',
                text: 'Dify、Coze等。拖拽锁定的界面。需要为特定的工作方式仔细打造工作流。',
                verdict: '不适合复杂场景。'
            },
            punchline: 'NormCode（诺码）让你掌控——通过将最少形式化与自然语言结合的计划。无需编程。易读易运行，AI可直接生成。可扩展、可组合、可复用。'
        },
        // language: → loaded from lang/language-section.js
        whyLang: {
            title: '只有语言才能被学习',
            subtitle: '工具被使用。平台被订阅。语言成为你的思维方式。',
            learn: {
                title: '学一次，描述任何工作流',
                text: '就像SQL之于数据库——学习NormCode，你就能描述任何AI智能体工作流。不绑定任何特定框架、模型或平台。'
            },
            debug: {
                title: '每个步骤都可以独立调试',
                text: '没有全局上下文意味着每个步骤都有已知的、有界的输入集。独立调试单个步骤。出问题时，检查输入——它们就在缩进中。'
            },
            artifact: {
                title: '计划是你的产物',
                text: '.ncds文件是可移植的文本文档。用Git进行版本控制。与团队共享。带到任何编排器。无供应商锁定。'
            }
        },
        lifecycle: {
            title: '描述 → 编译 → 审查 → 运行 → 修改 → 部署',
            step1: { title: '描述', text: '编写计划——或让AI从描述中生成它' },
            step2: { title: '编译', text: '编译器将其转换为可执行工作流。' },
            step3: { title: '审查', text: '在运行前阅读每个步骤。经理可以批准它。' },
            step4: { title: '运行', text: '编排器运行每个步骤。每个输入/输出都有记录。' },
            step5: { title: '修改', text: '修改一个步骤而不破坏其他步骤。从任何检查点分叉。' },
            step6: { title: '部署', text: '上线发布。文件是你的——Git它、发布它、交给同事。' }
        },
        seeIt: {
            title: '从计划到输出——观看真实智能体运行',
            subtitle: '查看NormCode Canvas实际运行，或自己尝试一个实时AI智能体。',
            videoLabel: 'Canvas 演示',
            clickToPlay: '点击播放演示',
            videoCaption: '可视化设计、调试和运行NormCode计划',
            demoTitle: '实时演示 — PPT智能体',
            demoText: '由NormCode计划编排的真实AI智能体。给它一个主题 → 它生成完整的演示文稿。',
            tryIt: '自己试试 →'
        },
        properties: {
            title: '为真正的复杂性而构建',
            subtitle: '想深入了解的技术细节——以下是底层机制。',
            semantic: { title: '语义 vs. 语法', text: '只有推理消耗token。数据路由、筛选和循环始终免费。' },
            parallel: { title: '并行执行', text: '独立步骤同时运行。无需手动线程管理。' },
            checkpoint: { title: '检查点与恢复', text: '每个步骤都有SQLite状态。暂停、恢复、从任何位置分叉。' },
            patching: { title: '智能补丁', text: '修改一个步骤，只重新运行受影响的部分。缓存其余部分。' },
            flowIndex: { title: '流索引系统', text: '每个节点都有唯一地址。设置断点、跟踪日志、精确调试。' },
            compilation: { title: '渐进编译', text: '从描述到执行的4个阶段。检查每个阶段。' }
        },
        who: {
            title: '一个生态，覆盖每个角色。',
            subtitle: '六大产品，三种角色——各为最需要它的人而生。',
            designer: {
                tab: '智能体设计者',
                hint: '工程师与开发者',
                title: '构建智能',
                desc: '用NormCode设计智能体工作流，编译为可执行计划，部署自主AI智能体。',
                lang_desc: '用结构化、可读的语法定义工作流框架。',
                comp_desc: '通过4个编译阶段将计划转化为可执行工作流。',
                agent_desc: '执行单元——逐步运行编译后的工作流。'
            },
            operator: {
                tab: '产品运维者',
                hint: '管理者与运维团队',
                title: '管理与维护',
                desc: '检查每个步骤，通过完整审计跟踪调试，管理版本，维护共享工作空间。',
                canvas_desc: '可视化调试、逐步检查、完整的审计跟踪。',
                server_desc: '版本控制、共享工作空间和团队协作中心。'
            },
            enduser: {
                tab: '终端用户',
                hint: '领域专家与使用者',
                title: '使用成果',
                desc: '通过专用界面与AI智能体交互——无需技术知识。',
                clients_desc: '为每个场景定制的交互界面——对话、表单、仪表板，满足工作流所需。'
            },
            language: { name: '诺码语言' },
            compiler: { name: '编译器' },
            agent:    { name: '流程代理' },
            canvas:   { name: '画布' },
            server:   { name: '服务器' },
            clients:  { name: '客户端' }
        },
        getStarted: {
            title: '从这里开始',
            see: {
                title: '先看看',
                desc: '我想先了解再决定。',
                link1: '试试实时PPT智能体'
            },
            learn: {
                title: '学习语言',
                desc: '我想了解它是如何工作的。',
                link1: '阅读语法（3个符号）',
                link2: '浏览示例',
                link3: '了解编译过程'
            },
            build: {
                title: '开始构建',
                desc: '我准备好试试了。',
                link1: '下载 Canvas',
                link2: '打开示例项目',
                link3: '阅读文档'
            }
        },
        footer: {
            tagline: 'AI智能体的工作语言',
            paper: '研究论文',
            contact: '联系我们',
            office: '广州市南沙区黄阁镇海滨路创享湾4栋TIMETABLE粤港澳青创基地'
        }
    }
});

