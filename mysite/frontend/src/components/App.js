import React, {Component} from "react";
import {render} from "react-dom";


function Greeting(props) {
    if(localStorage['prefs'] == null) {
        return (
            <div>New Session</div>
        );
    }
    return(
        <div>Existing Session</div>
    );
}

function VoteButton(props) {
    return (
        <button id="{props.name}" type="button">{props.text}</button>
    );
}

function UserInput(props) {
    return (
        <div className="UserInput">
        <label for="{props.id}">{props.pos}</label>
        <input type = "text" id="{props.id}" name= "{props.id}"></input>
        </div>
    );
}

class App extends Component {
    constructor(props) {
        super(props);
        this.state = {
            data: [],
            loaded: false,
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
            <VoteButton name="up" text="Loved it!" />
            <VoteButton name="down" text ="I don't like this topic." />
            </div>
            </div>
        );
    }
}

export default App;
const container = document.getElementById("app");
render(<App />, container);