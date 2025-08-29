import { useEffect, useState } from "react";
import axios from "axios";
import Admin from "./Admin.jsx";
import { StrictMode } from "react";

function AdminPanel() {
    return (
        <div>
            <nav>
                <button>
                    <StrictMode>
                        <Admin />
                    </StrictMode>
                </button>
            </nav>
        </div>
    );
}

export default AdminPanel;