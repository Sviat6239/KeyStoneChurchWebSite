<script lang="ts">
    import { login } from "../auth";
    import { loginAPI } from "../api";

    let loginInput = "";
    let password = "";
    let error = "";

    async function submit() {
        error = "";
        try {
            const data = await loginAPI(loginInput, password);
            if (data.token) {
                login(data.token);
                loginInput = "";
                password = "";
            } else if (data.error) {
                error = data.error;
            }
        } catch (e) {
            error = "Login failed";
        }
    }
</script>

<div>
    <input placeholder="Login" bind:value={loginInput} />
    <input type="password" placeholder="Password" bind:value={password} />
    <button on:click={submit}>Login</button>
    {#if error}<p style="color:red">{error}</p>{/if}
</div>
