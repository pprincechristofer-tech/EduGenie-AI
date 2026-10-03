// ============================================================
// EDUGENIE FRONTEND JAVASCRIPT
// ============================================================


// ============================================================
// GET ELEMENT
// ============================================================

function getElement(id) {

    return document.getElementById(id);

}


// ============================================================
// SHOW LOADING
// ============================================================

function showLoading(element, message) {

    element.innerHTML = `
        <div class="loading">

            <div class="spinner"></div>

            <span>${message}</span>

        </div>
    `;

}


// ============================================================
// SHOW ERROR
// ============================================================

function showError(element, message) {

    element.innerHTML = `
        <div style="
            color:#dc2626;
            background:#fef2f2;
            padding:15px;
            border-radius:10px;
        ">
            ❌ ${escapeHtml(message)}
        </div>
    `;

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent =
        text;

    return div.innerHTML;

}


// ============================================================
// ASK QUESTION
// ============================================================

async function askQuestion() {

    const question =
        getElement("question")
            .value
            .trim();

    const subject =
        getElement("subject")
            .value;

    const level =
        getElement("level")
            .value;

    const mode =
        getElement("mode")
            .value;

    const section =
        getElement("answerSection");

    const answer =
        getElement("answer");

    const button =
        getElement("askButton");


    // Validate

    if (!question) {

        alert(
            "Please enter your question first."
        );

        getElement("question").focus();

        return;

    }


    // Show result

    section.classList.remove(
        "hidden"
    );


    button.disabled = true;


    showLoading(
        answer,
        "EduGenie is thinking..."
    );


    // Scroll to result

    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });


    try {

        const response =
            await fetch(
                "/api/ask",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        question:
                            question,

                        subject:
                            subject,

                        level:
                            level,

                        mode:
                            mode

                    })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to get an answer."
            );

        }


        answer.textContent =
            data.answer;


    }
    catch (error) {

        console.error(
            "Ask Error:",
            error
        );

        showError(
            answer,
            error.message
        );

    }
    finally {

        button.disabled = false;

    }

}


// ============================================================
// SUMMARIZE
// ============================================================

async function summarizeText() {

    const text =
        getElement("summaryText")
            .value
            .trim();

    const section =
        getElement("summarySection");

    const result =
        getElement("summaryResult");


    if (!text) {

        alert(
            "Please paste your study material first."
        );

        getElement("summaryText").focus();

        return;

    }


    section.classList.remove(
        "hidden"
    );


    showLoading(
        result,
        "Creating your study summary..."
    );


    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });


    try {

        const response =
            await fetch(
                "/api/summarize",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        text: text
                    })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to summarize the material."
            );

        }


        result.textContent =
            data.summary;


    }
    catch (error) {

        console.error(
            "Summary Error:",
            error
        );

        showError(
            result,
            error.message
        );

    }

}


// ============================================================
// GENERATE QUIZ
// ============================================================

async function generateQuiz() {

    const topic =
        getElement("quizTopic")
            .value
            .trim();

    const number =
        Number(
            getElement("quizNumber")
                .value
        );

    const section =
        getElement("quizSection");

    const result =
        getElement("quizResult");


    if (!topic) {

        alert(
            "Please enter a quiz topic."
        );

        getElement("quizTopic").focus();

        return;

    }


    section.classList.remove(
        "hidden"
    );


    showLoading(
        result,
        "Generating your AI quiz..."
    );


    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });


    try {

        const response =
            await fetch(
                "/api/quiz",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        topic:
                            topic,

                        number:
                            number

                    })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to generate quiz."
            );

        }


        if (
            !Array.isArray(data.questions) ||
            data.questions.length === 0
        ) {

            throw new Error(
                "The AI did not return any quiz questions. Please try again."
            );

        }


        renderQuiz(
            data.questions,
            result
        );


    }
    catch (error) {

        console.error(
            "Quiz Error:",
            error
        );

        showError(
            result,
            error.message
        );

    }

}


function renderQuiz(questions, result) {

    result.replaceChildren();


    questions.forEach(function (question, questionIndex) {

        const questionCard =
            document.createElement("article");

        questionCard.className =
            "quiz-question";


        const heading =
            document.createElement("h3");

        heading.className =
            "quiz-question-heading";

        heading.textContent =
            `Question ${questionIndex + 1}`;


        const prompt =
            document.createElement("p");

        prompt.className =
            "quiz-question-prompt";

        prompt.textContent =
            question.question;


        const form =
            document.createElement("form");


        const fieldset =
            document.createElement("fieldset");

        fieldset.className =
            "quiz-options";


        const legend =
            document.createElement("legend");

        legend.textContent =
            "Choose one answer";

        fieldset.appendChild(legend);


        question.choices.forEach(function (choice) {

            const label =
                document.createElement("label");

            label.className =
                "quiz-choice";


            const input =
                document.createElement("input");

            input.type =
                "radio";

            input.name =
                `quiz-question-${questionIndex}`;

            input.value =
                choice.label;

            input.required =
                true;


            const choiceText =
                document.createElement("span");

            choiceText.textContent =
                `${choice.label}. ${choice.text}`;


            label.append(
                input,
                choiceText
            );

            fieldset.appendChild(label);

        });


        const checkButton =
            document.createElement("button");

        checkButton.type =
            "submit";

        checkButton.className =
            "secondary-button quiz-check-button";

        checkButton.textContent =
            "Check answer";


        const feedback =
            document.createElement("p");

        feedback.className =
            "quiz-feedback";

        feedback.setAttribute(
            "aria-live",
            "polite"
        );

        feedback.hidden =
            true;


        form.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();

                const selected =
                    fieldset.querySelector("input:checked");

                if (!selected) {

                    return;

                }


                const isCorrect =
                    selected.value === question.correct_answer;

                const correctChoice =
                    question.choices.find(function (choice) {
                        return choice.label === question.correct_answer;
                    });


                feedback.classList.add(
                    isCorrect ? "is-correct" : "is-incorrect"
                );

                feedback.textContent = isCorrect
                    ? `Correct! ${question.explanation}`
                    : `Not quite. The correct answer is ${question.correct_answer}. ${correctChoice.text} ${question.explanation}`;

                feedback.hidden =
                    false;

                fieldset.disabled =
                    true;

                checkButton.disabled =
                    true;

            }
        );


        form.append(
            fieldset,
            checkButton,
            feedback
        );

        questionCard.append(
            heading,
            prompt,
            form
        );

        result.appendChild(
            questionCard
        );

    });

}


// ============================================================
// GENERATE STUDY PLAN
// ============================================================

async function generateStudyPlan() {

    const subject =
        getElement("planSubject")
            .value
            .trim();

    const days =
        Number(
            getElement("planDays")
                .value
        );

    const hours =
        Number(
            getElement("planHours")
                .value
        );

    const section =
        getElement("planSection");

    const result =
        getElement("planResult");


    if (!subject) {

        alert(
            "Please enter a subject."
        );

        getElement("planSubject").focus();

        return;

    }


    section.classList.remove(
        "hidden"
    );


    showLoading(
        result,
        "Creating your personalized study plan..."
    );


    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });


    try {

        const response =
            await fetch(
                "/api/study-plan",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        subject:
                            subject,

                        days:
                            days,

                        hours:
                            hours

                    })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to create study plan."
            );

        }


        result.textContent =
            data.plan;


    }
    catch (error) {

        console.error(
            "Study Plan Error:",
            error
        );

        showError(
            result,
            error.message
        );

    }

}


// ============================================================
// COPY RESULT
// ============================================================

async function copyResult(id) {

    const element =
        getElement(id);

    const text =
        element.innerText ||
        element.textContent;


    if (!text) {

        return;

    }


    try {

        await navigator.clipboard.writeText(
            text
        );

        alert(
            "Copied successfully!"
        );

    }
    catch (error) {

        console.error(
            "Copy Error:",
            error
        );

        alert(
            "Unable to copy."
        );

    }

}


// ============================================================
// CTRL + ENTER
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const question =
            getElement("question");


        question.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    event.ctrlKey
                ) {

                    event.preventDefault();

                    askQuestion();

                }

            }
        );


        // Health check

        checkBackend();

    }
);


// ============================================================
// BACKEND HEALTH CHECK
// ============================================================

async function checkBackend() {

    try {

        const response =
            await fetch(
                "/api/health"
            );


        const data =
            await response.json();


        if (data.success) {

            console.log(
                "EduGenie backend connected successfully."
            );

        }

    }
    catch (error) {

        console.error(
            "Backend connection error:",
            error
        );

    }

}