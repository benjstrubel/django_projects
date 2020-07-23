import React, {Component} from "react";
import {render} from "react-dom";

const INCREMENT_SIZE = .2;
var testjson = {"words": ["Hello", "{0}", "this", "is", "a", "{0}", "cool", "sports", "test", "message", "."],
"pos": ["INTJ", "NOUN", "DET", "AUX", "DET", "ADV", "ADJ", "NOUN", "NOUN", "NOUN", "PUNCT"]};

function MainContent(props) {
    const elements = [];

    for(var i = 0; i < testjson["words"].length -1;++i) {
        if(testjson["words"][i] == "{0}") {
            var pos = testjson["pos"][i];
            elements.push(<UserInput id={i} pos={pos} key={i} />)
        }
    }

    return(
        <div>
            {elements}
        </div>
    );
}

function Greeting(props) {
    if(localStorage['entertainment'] == null) {
        localStorage['entertainment'] = 0.0;
        localStorage['health'] = 0.0;
        localStorage['politics'] = 0.0;
        localStorage['sports'] = 0.0;
        localStorage['tech'] = 0.0;
        return (
            <div>
            Hiya User,<br/>
            It seems you're new here. What's for favorite topic for a game?<br/>
            <UpVoteButton id="entertainment" name="Entertainment"/>
            <UpVoteButton id="health" name="Health" />
            <UpVoteButton id="politics" name="Politics" />
            <UpVoteButton id="sports" name = "Sports"/>
            <UpVoteButton id="tech" name = "Tech"/>
            </div>
        );
    }
    return(
        <div>Welcome Back Old Friend!</div>
    );
}

function downVote(name) {
    localStorage[name] -= INCREMENT_SIZE;
    if (localStorage[name] < 0) {
        localStorage[name] = 0;
    }
}

function upVote(name) {
    localStorage[name] += INCREMENT_SIZE;
    if (localStorage[name] > 1) {
        localStorage[name] = .99;
    }
}

function DownVoteButton(props) {
    return (
        <button id={props.id} type="button">{props.name}</button>
    );
}

function UpVoteButton(props) {
    return (
        <button id={props.id} type="button">{props.name}</button>
    );
}

function SubmitButton(props) {
    return (
        <button id="submit" type="button" onClick={ShowResult}>Let Me See My Creation</button>
    );
}

function UserInput(props) {
    return (
        <div className="UserInput">
        <label for={props.id}>{props.pos}</label>
        <input type = "text" id={props.id} name= {props.id}></input>
        </div>
    );
}

function ShowResult(props) {
    console.log("showing result");
    return(
        <div>
        I'm a result
        </div>
    );
}

class App extends Component {
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            loaded: false,
            inputs: [],
            placeholder: "Loading"
        };
    }

    componentDidMount() {
        fetch("api/wordgame")
            .then(response => {
                if(response.status > 400) {
                    return this.setState(() => {
                        return { placeholder: "Something went wrong!"};
                    });
                }
                return response.json();
            })
            .then(data => {
                this.setState(() => {
                    return {
                        data,
                        loaded: true
                    };
                });
            });
    }

    render() {
        return (
            <div>
                <Greeting />
            <ul>
            {this.state.data.map(blurb => {
                return (
                    <li key={blurb.id}> {blurb.text}</li>
                );
            })}
            </ul>
            
            <div>
            <MainContent />
            <SubmitButton />
            <br/>
            <UpVoteButton id="health" name="Loved it!" />
            <DownVoteButton id="health" name ="I don't like this topic." />
            </div>
            </div>
        );
    }
}

export default App;
const container = document.getElementById("app");
render(<App />, container);