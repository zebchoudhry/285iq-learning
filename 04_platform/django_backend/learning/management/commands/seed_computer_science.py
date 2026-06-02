"""
Seed GCSE Computer Science curriculum: subject, topics, lessons, and questions.
Aligned to AQA 8525 specification.

Usage: python manage.py seed_computer_science [--questions-per-lesson 5]

Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand

from learning.models import Subject, Topic, Lesson, Question


CS_CURRICULUM = [
    (
        "Systems Architecture",
        "CPU, memory, storage, and Von Neumann architecture",
        [
            ("The Von Neumann Architecture", [
                ("What are the four main components of the Von Neumann architecture?",
                 "Control Unit (CU), Arithmetic Logic Unit (ALU), Memory (RAM), and Input/Output devices.",
                 "multiple_choice", 1),
                ("Describe the role of the Control Unit (CU) in a CPU.",
                 "The Control Unit fetches instructions from memory, decodes them, and coordinates the execution by sending control signals to other components.",
                 "short_answer", 2),
                ("What is the purpose of the Program Counter (PC) register?",
                 "The Program Counter holds the memory address of the next instruction to be fetched and executed.",
                 "short_answer", 1),
                ("What does MAR stand for and what does it do?",
                 "MAR stands for Memory Address Register. It holds the address in memory that the CPU wants to read from or write to.",
                 "short_answer", 1),
                ("What does MDR stand for and what does it do?",
                 "MDR stands for Memory Data Register. It holds the data that has been fetched from memory or is about to be written to memory.",
                 "short_answer", 1),
            ]),
            ("The Fetch-Decode-Execute Cycle", [
                ("Describe the three stages of the fetch-decode-execute cycle.",
                 "Fetch: the CPU retrieves the next instruction from memory using the address in the PC. Decode: the Control Unit interprets the instruction. Execute: the ALU or other components carry out the instruction.",
                 "calculation", 3),
                ("During the fetch stage, which register is updated to point to the next instruction?",
                 "The Program Counter (PC) is incremented to point to the next instruction.",
                 "short_answer", 1),
                ("What happens to the MDR during the fetch stage?",
                 "The contents of the memory address held in the MAR are copied into the MDR.",
                 "short_answer", 1),
            ]),
            ("CPU Performance Factors", [
                ("State three factors that affect the performance of a CPU.",
                 "Clock speed (measured in GHz), number of cores, and cache size.",
                 "short_answer", 3),
                ("Explain how increasing the clock speed affects CPU performance.",
                 "A higher clock speed means the CPU can complete more fetch-decode-execute cycles per second, so it can process instructions faster. However, this also generates more heat.",
                 "short_answer", 2),
                ("What is the difference between a dual-core and a quad-core processor?",
                 "A dual-core processor has two independent processing units (cores), while a quad-core has four. More cores allow more tasks to be processed simultaneously.",
                 "short_answer", 2),
            ]),
        ],
    ),
    (
        "Memory & Storage",
        "RAM, ROM, secondary storage, and data units",
        [
            ("RAM and ROM", [
                ("What does RAM stand for and what is its purpose?",
                 "RAM stands for Random Access Memory. It stores data and instructions that the CPU is currently using. It is volatile — data is lost when power is removed.",
                 "short_answer", 2),
                ("What does ROM stand for and how does it differ from RAM?",
                 "ROM stands for Read-Only Memory. Unlike RAM, ROM is non-volatile (retains data when power is off) and cannot normally be written to.",
                 "short_answer", 2),
                ("Why is RAM described as volatile memory?",
                 "Because the data stored in RAM is lost when the computer is switched off or power is removed.",
                 "short_answer", 1),
            ]),
            ("Secondary Storage", [
                ("Give two examples of secondary storage devices.",
                 "Hard Disk Drive (HDD) and Solid State Drive (SSD). (Also acceptable: USB flash drive, optical disc e.g. DVD.)",
                 "short_answer", 2),
                ("State two advantages of SSDs over HDDs.",
                 "SSDs are faster, more durable (no moving parts), lighter, and quieter than HDDs.",
                 "short_answer", 2),
                ("State two advantages of HDDs over SSDs.",
                 "HDDs are cheaper per gigabyte of storage and available in larger capacities.",
                 "short_answer", 2),
            ]),
            ("Data Units and Conversions", [
                ("How many bytes are in 1 kilobyte (using binary prefixes)?",
                 "1 kilobyte = 1,024 bytes.",
                 "short_answer", 1),
                ("Convert 2 GB to MB.",
                 "2 GB = 2 × 1,024 = 2,048 MB.",
                 "calculation", 2),
                ("A file is 4,096 KB. Convert this to MB.",
                 "4,096 KB ÷ 1,024 = 4 MB.",
                 "calculation", 2),
            ]),
        ],
    ),
    (
        "Networks",
        "Network types, protocols, topologies, and security",
        [
            ("Types of Networks", [
                ("What is the difference between a LAN and a WAN?",
                 "A LAN (Local Area Network) covers a small geographic area such as a single building. A WAN (Wide Area Network) covers a large geographic area, such as a country or the entire world (e.g. the internet).",
                 "short_answer", 2),
                ("State two advantages of networking computers.",
                 "Sharing resources (e.g. printers, files), easier communication (email, messaging), centralised data storage/backup, software can be updated across all machines simultaneously.",
                 "short_answer", 2),
                ("What is a client-server network?",
                 "A network where a central server provides services (files, emails, authentication) to client computers that request them.",
                 "short_answer", 2),
            ]),
            ("Network Protocols", [
                ("What does TCP/IP stand for?",
                 "Transmission Control Protocol / Internet Protocol.",
                 "short_answer", 1),
                ("Describe the role of HTTP and HTTPS in web communication.",
                 "HTTP (HyperText Transfer Protocol) defines how web pages are requested and served. HTTPS is the secure version, using encryption (TLS/SSL) to protect data in transit.",
                 "short_answer", 2),
                ("What is the purpose of DNS?",
                 "DNS (Domain Name System) translates human-readable domain names (e.g. www.bbc.co.uk) into IP addresses that computers use to identify each other on a network.",
                 "short_answer", 2),
                ("What is an IP address?",
                 "A unique numerical label assigned to each device on a network that identifies it and allows data to be routed to it.",
                 "short_answer", 1),
            ]),
            ("Network Security", [
                ("Name three common network security threats.",
                 "Malware (viruses, ransomware), phishing, denial-of-service (DoS) attacks, man-in-the-middle attacks, SQL injection.",
                 "short_answer", 3),
                ("What is a firewall and how does it protect a network?",
                 "A firewall monitors and controls incoming and outgoing network traffic based on security rules, blocking unauthorised access while allowing legitimate traffic.",
                 "short_answer", 2),
                ("Explain how encryption protects data on a network.",
                 "Encryption converts data into an unreadable format (ciphertext) using a key. Only someone with the correct decryption key can read the data, so intercepted data cannot be understood.",
                 "short_answer", 2),
            ]),
        ],
    ),
    (
        "Data Representation",
        "Binary, hexadecimal, character encoding, images, sound",
        [
            ("Binary and Denary", [
                ("Convert the binary number 11010110 to denary.",
                 "11010110 in binary = 128+64+0+16+0+4+2+0 = 214 in denary.",
                 "calculation", 2),
                ("Convert the denary number 75 to binary.",
                 "75 = 64+8+2+1 = 01001011 in binary.",
                 "calculation", 2),
                ("What is the largest denary value that can be stored in 8 bits?",
                 "255 (2^8 - 1 = 255).",
                 "short_answer", 1),
            ]),
            ("Hexadecimal", [
                ("Why is hexadecimal used in computing?",
                 "Hexadecimal is a compact way to represent binary data. Each hex digit represents exactly 4 bits, making it easier for humans to read and write binary values.",
                 "short_answer", 2),
                ("Convert 0xAF to denary.",
                 "A = 10, F = 15. 0xAF = (10 × 16) + 15 = 160 + 15 = 175.",
                 "calculation", 2),
                ("Convert the binary 11110000 to hexadecimal.",
                 "Split into nibbles: 1111 = F, 0000 = 0. Answer: 0xF0.",
                 "calculation", 2),
            ]),
            ("Character Encoding", [
                ("What is ASCII?",
                 "ASCII (American Standard Code for Information Interchange) is a character encoding standard that assigns a 7-bit binary code to each character (letters, digits, symbols).",
                 "short_answer", 2),
                ("What advantage does Unicode have over ASCII?",
                 "Unicode can represent a much larger number of characters (over 1 million) including characters from all world languages, whereas ASCII is limited to 128 characters.",
                 "short_answer", 2),
            ]),
            ("Images and Sound", [
                ("What is meant by the resolution of a digital image?",
                 "Resolution is the number of pixels in an image, usually expressed as width × height (e.g. 1920 × 1080). Higher resolution means more detail but a larger file size.",
                 "short_answer", 2),
                ("How does colour depth affect the quality and size of an image?",
                 "Greater colour depth means more bits per pixel, so more colours can be represented. This improves quality but increases file size.",
                 "short_answer", 2),
                ("Calculate the uncompressed file size of an image that is 800 × 600 pixels with a colour depth of 24 bits.",
                 "File size = 800 × 600 × 24 = 11,520,000 bits = 1,440,000 bytes = 1,440 KB ≈ 1.37 MB.",
                 "calculation", 3),
            ]),
        ],
    ),
    (
        "Computer Science Fundamentals",
        "Algorithms, pseudocode, flowcharts, searching and sorting",
        [
            ("Algorithms and Pseudocode", [
                ("What is an algorithm?",
                 "A step-by-step set of instructions to solve a problem or complete a task.",
                 "short_answer", 1),
                ("Write pseudocode to find the largest number in a list of n numbers.",
                 "max ← list[0]\nFOR i ← 1 TO n-1\n  IF list[i] > max THEN\n    max ← list[i]\n  ENDIF\nENDFOR\nOUTPUT max",
                 "extended", 3),
                ("What is the difference between a while loop and a for loop?",
                 "A FOR loop repeats a fixed number of times (count-controlled). A WHILE loop repeats as long as a condition is true (condition-controlled), so the number of iterations may vary.",
                 "short_answer", 2),
            ]),
            ("Searching Algorithms", [
                ("Describe the linear search algorithm.",
                 "Start at the first element. Compare each element in turn to the target. Return the position if found. If the end of the list is reached without finding it, return 'not found'. Works on unsorted lists.",
                 "short_answer", 3),
                ("Describe the binary search algorithm.",
                 "Start with the whole sorted list. Find the middle element. If it equals the target, return it. If target is smaller, search the left half; if larger, search the right half. Repeat until found or no elements remain.",
                 "short_answer", 3),
                ("State one advantage and one disadvantage of binary search compared to linear search.",
                 "Advantage: Binary search is much faster for large sorted lists (O(log n) vs O(n)). Disadvantage: Binary search requires the list to be sorted first.",
                 "short_answer", 2),
            ]),
            ("Sorting Algorithms", [
                ("Describe how bubble sort works.",
                 "Repeatedly step through the list, compare adjacent pairs, and swap them if they are in the wrong order. Repeat until no swaps are needed. The largest values 'bubble' to the end.",
                 "short_answer", 3),
                ("Describe how merge sort works.",
                 "Divide the list in half repeatedly until each sublist has one element. Then merge pairs of sublists back together in sorted order until the whole list is sorted.",
                 "short_answer", 3),
                ("What is the time complexity of bubble sort in the worst case?",
                 "O(n²) — where n is the number of elements.",
                 "short_answer", 2),
            ]),
        ],
    ),
    (
        "Programming Concepts",
        "Variables, data types, selection, iteration, subroutines, and file handling",
        [
            ("Variables and Data Types", [
                ("Name four common data types used in programming.",
                 "Integer (whole number), float/real (decimal), string (text), boolean (True/False). Also: character, list/array.",
                 "short_answer", 2),
                ("What is a constant and how does it differ from a variable?",
                 "A constant holds a value that cannot be changed during program execution. A variable holds a value that can change.",
                 "short_answer", 2),
                ("What is casting? Give an example.",
                 "Casting is converting a value from one data type to another. Example: int('42') converts the string '42' to the integer 42.",
                 "short_answer", 2),
            ]),
            ("Selection and Iteration", [
                ("Write pseudocode using an IF statement to output whether a number is positive, negative, or zero.",
                 "INPUT num\nIF num > 0 THEN\n  OUTPUT 'Positive'\nELSEIF num < 0 THEN\n  OUTPUT 'Negative'\nELSE\n  OUTPUT 'Zero'\nENDIF",
                 "extended", 3),
                ("What is the difference between a definite and an indefinite loop?",
                 "A definite loop (FOR loop) runs a fixed number of times. An indefinite loop (WHILE or REPEAT-UNTIL) runs until a condition changes.",
                 "short_answer", 2),
            ]),
            ("Subroutines", [
                ("What is a subroutine (procedure/function) and why is it useful?",
                 "A subroutine is a named block of code that can be called multiple times. It makes programs shorter, easier to read, easier to debug, and promotes code reuse.",
                 "short_answer", 3),
                ("What is the difference between a procedure and a function?",
                 "A function returns a value; a procedure does not return a value.",
                 "short_answer", 1),
                ("What are parameters in a subroutine?",
                 "Parameters are variables listed in the subroutine definition that receive values (arguments) passed to the subroutine when it is called.",
                 "short_answer", 2),
            ]),
        ],
    ),
    (
        "Boolean Logic & Logic Gates",
        "Truth tables, logic gates, Boolean expressions",
        [
            ("Logic Gates", [
                ("State the output of an AND gate when both inputs are 1.",
                 "1 (True). AND gate outputs 1 only when ALL inputs are 1.",
                 "short_answer", 1),
                ("Complete the truth table for an OR gate with inputs A and B.",
                 "A=0,B=0→0; A=0,B=1→1; A=1,B=0→1; A=1,B=1→1",
                 "short_answer", 2),
                ("Describe the behaviour of a NOT gate.",
                 "A NOT gate (inverter) has one input and one output. It outputs the opposite of its input: 0→1, 1→0.",
                 "short_answer", 1),
                ("What does a NAND gate output when both inputs are 1?",
                 "0. NAND is NOT AND — it outputs 0 only when all inputs are 1.",
                 "short_answer", 1),
            ]),
            ("Boolean Expressions", [
                ("Write the Boolean expression for: output is 1 only if A is 1 AND B is 0.",
                 "Q = A AND NOT B  (or: Q = A · B̄)",
                 "short_answer", 2),
                ("Simplify the expression: A AND TRUE.",
                 "A (anything ANDed with TRUE equals itself).",
                 "short_answer", 1),
                ("What is De Morgan's first law?",
                 "NOT (A OR B) = (NOT A) AND (NOT B)",
                 "short_answer", 2),
            ]),
        ],
    ),
    (
        "Cyber Security",
        "Threats, social engineering, protection methods, and ethics",
        [
            ("Cyber Threats", [
                ("What is malware? Give three examples.",
                 "Malware is malicious software designed to damage or gain unauthorised access to systems. Examples: virus, worm, ransomware, trojan, spyware.",
                 "short_answer", 3),
                ("What is a phishing attack?",
                 "A phishing attack is a social engineering technique where attackers send fraudulent emails or messages that appear to come from a trusted source, tricking victims into revealing passwords or personal information.",
                 "short_answer", 2),
                ("What is SQL injection and how can it be prevented?",
                 "SQL injection is an attack where malicious SQL code is inserted into an input field to manipulate a database. It can be prevented using parameterised queries / prepared statements.",
                 "short_answer", 3),
            ]),
            ("Protection and Ethics", [
                ("State three ways to protect a computer system from cyber attacks.",
                 "Use strong/unique passwords, enable two-factor authentication, install and update antivirus software, use a firewall, keep software updated/patched, encrypt data.",
                 "short_answer", 3),
                ("What is the purpose of the Computer Misuse Act 1990?",
                 "It criminalises unauthorised access to computer systems, unauthorised access with intent to commit further offences, and unauthorised modification of computer material.",
                 "short_answer", 2),
                ("What is two-factor authentication (2FA) and why is it more secure than a password alone?",
                 "2FA requires two forms of verification (e.g. password + SMS code). Even if a password is stolen, the attacker still cannot log in without the second factor.",
                 "short_answer", 2),
            ]),
        ],
    ),
]


class Command(BaseCommand):
    help = "Seed GCSE Computer Science curriculum (AQA 8525 aligned)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Print counts without writing")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        subject, s_created = Subject.objects.get_or_create(
            name="computer_science",
            exam_board=None,
            tier="higher",
            defaults={
                "display_name": "Computer Science",
                "description": "GCSE Computer Science — AQA 8525. Systems, networks, programming, algorithms, data, and cyber security.",
                "is_active": True,
            },
        )
        if not dry_run and not s_created:
            subject.is_active = True
            subject.save(update_fields=["is_active"])

        verb = "Would create" if dry_run else "Created/updated"
        self.stdout.write(f"Subject: Computer Science ({'new' if s_created else 'existing'})")

        topics_created = lessons_created = questions_created = 0

        for t_order, (topic_name, topic_desc, topic_lessons) in enumerate(CS_CURRICULUM, start=1):
            if not dry_run:
                topic, tc = Topic.objects.get_or_create(
                    subject=subject,
                    name=topic_name,
                    defaults={
                        "description": topic_desc,
                        "order": t_order,
                        "is_active": True,
                    },
                )
                if tc:
                    topics_created += 1
            else:
                topic = None
                topics_created += 1

            for l_order, (lesson_title, questions) in enumerate(topic_lessons, start=1):
                if not dry_run:
                    lesson, lc = Lesson.objects.get_or_create(
                        topic=topic,
                        title=lesson_title,
                        defaults={
                            "content": f"GCSE Computer Science: {lesson_title}",
                            "estimated_duration": 20,
                            "lesson_type": "practice",
                            "difficulty_level": 2,
                            "key_skills": [],
                            "order": l_order,
                            "is_active": True,
                        },
                    )
                    if lc:
                        lessons_created += 1
                else:
                    lesson = None
                    lessons_created += 1

                for q_text, q_answer, q_type, q_marks in questions:
                    if not dry_run:
                        _, qc = Question.objects.get_or_create(
                            lesson=lesson,
                            question_text=q_text,
                            defaults={
                                "correct_answer": q_answer,
                                "explanation": q_answer,
                                "question_type": q_type,
                                "difficulty_level": min(q_marks + 1, 5),
                                "marks_available": q_marks,
                                "source": "cs_seed",
                                "is_active": True,
                            },
                        )
                        if qc:
                            questions_created += 1
                    else:
                        questions_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"{verb}: {topics_created} topics, {lessons_created} lessons, {questions_created} questions."
        ))
