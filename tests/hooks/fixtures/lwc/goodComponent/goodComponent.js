import { LightningElement, api, wire } from 'lwc';
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

export default class GoodComponent extends LightningElement {
    @api recordId;
    accounts = [];
    error;

    @wire(getAccounts, { recordId: '$recordId' })
    wiredAccounts({ error, data }) {
        if (data) {
            this.accounts = data;
            this.error = undefined;
        } else if (error) {
            this.error = error;
            this.accounts = [];
        }
    }

    get hasAccounts() {
        return this.accounts.length > 0;
    }

    get cardTitle() {
        return `Accounts (${this.accounts.length})`;
    }

    get items() {
        return this.accounts.map((acc) => ({
            id: acc.Id,
            name: acc.Name,
        }));
    }

    handleRefresh() {
        this.accounts = [];
    }
}
