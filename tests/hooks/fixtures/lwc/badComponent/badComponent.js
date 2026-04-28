import { LightningElement } from 'lwc';

export default class BadComponent extends LightningElement {
    firstName = 'John';
    lastName = 'Doe';
    items = [];
    count = 0;

    connectedCallback() {
        // Direct DOM manipulation
        this.template.querySelector('.my-class').style.color = 'red';
        document.getElementById('foo');
    }

    handleClick(event) {
        // Hardcoded style
        event.target.style.background = 'blue';
        this.count = this.count + 1;
    }
}
