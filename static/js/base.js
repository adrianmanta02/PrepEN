const registerForm = document.getElementById('registerForm'); 
if (registerForm) {
       registerForm.addEventListener('submit', async function (event) {
        event.preventDefault(); 

        const form = event.target; 
        const formData = new FormData(form); 

        // convert into JSON
        const data = Object.fromEntries(formData.entries()); 

        // check password matching 
        if (data.password !== data.password2)
        {
            alert("Parolele nu se potrivesc!"); 
            return; 
        }

        // prepare the payload for the request 
        const payload = {
            firstname: data.firstname, 
            lastname: data.lastname, 
            username: data.username, 
            email: data.email, 
            password: data.password, 
            grade: data.grade
        }; 
    
        try { 
            const response = await fetch ('/auth/', {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json'
                }, 
                body: JSON.stringify(payload)
            });

            if (response.ok) { 
                window.location.href = "/auth/login-page"; 
            }
            else 
            { 
                // handle error 
                const errorData = await response.json(); 
                alert(`Error ${errorData.detail}`);
            }
        }
        catch(error) { 
            console.error('Error: ', error); 
            alert('An error occured. Please try again.'); 
        }
    }); 
}

const loginForm = document.getElementById('loginForm');
if (loginForm) { 
    console.log("Yay"); 
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault(); 
    
        const form = event.target; 
        const formData = new FormData(form);

        const payload = new URLSearchParams(); 
        for (const [key, value] of formData.entries()) { 
            payload.append(key, value); 
        }

        console.log(payload); 

        try { 
            const response = await fetch ('/auth/token', {
                method: 'POST', 
                headers: {
                    'Content-Type': "application/x-www-form-urlencoded", 
                }, 
                body: payload.toString()  
            }); 

            if (response.ok) { 
                const data = await response.json(); 

                // delete any cookies available 
                logout();

                // save token to cookie 
                document.cookie = `access_token=${data.access_token}; path=/`; 
                window.location.href = "/materials/main-page";
            }
            else { 
                const warningDiv = document.getElementById('errorPassword'); 
                if (response.status == 403) { 
                    warningDiv.textContent = "Contul este creat, dar trebuie să așteptați ca profesorul să accepte solicitarea!";
                } else { 
                    warningDiv.textContent = "Parola incorectă. Încercați din nou!";
                }
            }
        }
        catch (error) { 
            console.error("Error: ", error); 
            alert("An error occured. Please try again.");
        }
    }); 
} 

function logout() { 
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"; 
}

if (window.location.pathname == "/auth/register-page") { 
    const registerButton = document.querySelector('button[type="submit"]'); 

    const usernameField = document.getElementById('userName');
    if (usernameField) { 
        usernameField.addEventListener("blur", async (event) => { 
            const username = event.target.value; 
            if (username.trim() === "") return; // exit statement if no username typed in

            const response = await fetch(`/auth/check-username?username=${encodeURIComponent(username)}`);
            const data = await response.json(); 
            
            const errorDiv = document.getElementById('usernameError');
            if (errorDiv) { 
                if (!data.available) { 
                    errorDiv.textContent = "Acest username este luat deja, înregistrează-te cu altul!";
                    registerButton.disabled = true; 
                } else {
                    errorDiv.textContent = "";
                    registerButton.disabled = false;
                }
            } 
        }); 
    } 

    const emailField = document.getElementById('email');
    if (emailField) { 
        emailField.addEventListener("blur", async (event) => {
            const email = event.target.value; 
            if (email.trim() === "") return;

            const response = await fetch (`/auth/check-email?email=${encodeURIComponent(email)}`); 
            const data = await response.json(); 

            const errorDiv = document.getElementById("emailError");
            if (errorDiv) { 
                if (!data.available) { 
                    errorDiv.textContent = "Exista deja un cont asociat acestui email."; 
                    registerButton.disabled = true; 
                }
                else { 
                    errorDiv.textContent = "";
                    registerButton.disabled = false; 
                }
            } 
        });
    }

}

if (window.location.pathname == "/auth/login-page") { 
    const floatingInputField = document.getElementById("floatingInput"); 
    if (floatingInputField) { 
        floatingInputField.addEventListener("blur", async (event) => {
            const inputUsername = event.target.value; 
            if (inputUsername.trim() === "") { 
                return; 
            }

            const response = await fetch(`/auth/check-username?username=${encodeURIComponent(inputUsername)}`); 
            const data = await response.json();

            const loginButton = document.querySelector('button[type="submit"]'); 
            const errorDiv = document.getElementById('errorUsername'); 
            if (data.available) { 
                loginButton.disabled = true; 
                errorDiv.textContent = "Nu există cont cu acest nume de utilizator.";
            }
            else { 
                loginButton.disabled = false; 
                errorDiv.textContent = "";
            }
        }); 
    }
}

// Helper function to get cookie value
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}


const uploadForm = document.getElementById('uploadForm'); 
if (uploadForm) { 
    uploadForm.addEventListener("submit", async function (event) { 
        event.preventDefault(); 

        const form = event.target; 
        const formData = new FormData(form);

        const path = sessionStorage.getItem('currentPath') || '/materials'; 
        formData.append('path', path); 
        
        for (let[key, value] of formData.entries()) { 
            console.log(key, value); 
        }

        const urlParams = new URLSearchParams(window.location.search); 
        const materialId = Number(urlParams.get('materialId'));

        const token = getCookie('access_token'); 
        try {
            var response = ""; 
            if (!materialId) {
                response = await fetch("/materials/material", {
                    method: 'POST', // creating a new entry in the database
                    headers: { 
                        'Authorization': `Bearer ${token}`
                    }, 
                    body: formData, 
                    credentials: 'include' // send the jwt token to the backend to allow creating the new material
                });
            }
            else { 
                response = await fetch(`/materials/material/edit/${materialId}`, {
                    method: 'PUT', 
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }, 
                    body: formData, 
                    credentials: 'include'
                }); 
            }
            
            if (response.ok) { 
                if (materialId) { 
                    window.location.href = `/materials/view/${materialId}`; 
                }
                else window.location.href = "/materials/main-page"; 
            }
            else { 
                const errorData = await response.json(); 
                alert(`Error: ${errorData.detail}`); 
            }
        }   
        catch (error) { 
            console.error("Error: ", error); 
            alert("An error occured. Try again later.")
        }
    });
}

const deleteButton = document.getElementById('deleteButton'); 
if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
        const urlPath = window.location.pathname; 
        const pathParts = urlPath.split("/"); 
        const id = pathParts.pop(); 

        const token = getCookie('access_token'); 
         
        const response = await fetch(`/materials/material/${id}`, {
            method: 'DELETE', 
            headers:  {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }, 
            body: parseInt(id)
        }); 

        try { 
            if (response.ok) { 
                window.location.href = sessionStorage.getItem('currentPath') || "/materials"; 
            }
            else { 
                const errorData = await response.json(); 
                alert(`Error: ${errorData.detail}`); 
            }
        }
        catch (error) { 
            console.error(error.detail); 
            alert("An error occured. Please try again later");  
        }
    });
}

const discButton = document.getElementById('disconnectButton'); 
if (discButton) { 
    console.log('Im here');
    discButton.addEventListener("click", async (event) => {
        event.preventDefault(); 
        logout();   
        window.location.href = '/'; 
    }); 
}

const thumbnailInput = document.getElementById('thumbnail');
const thumbnailPreview = document.getElementById('thumbnail-preview');
const filenameDisplay = document.getElementById('filename');

if (thumbnailInput) { 
    thumbnailInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            // Update preview
            const reader = new FileReader();
            reader.onload = (e) => {
                thumbnailPreview.src = e.target.result;
            };
            reader.readAsDataURL(file);

            // Update filename
            filenameDisplay.innerHTML = file.name;
        } else {
            // Dacă nu mai e selectat niciun fișier
            thumbnailPreview.src = "/static/default-thumb.png";
            filenameDisplay.textContent = "Nicio imagine selectată";
        }
    });
}

async function removeFile(filename) {
    const urlParams = new URLSearchParams(window.location.search);
    const materialId = urlParams.get("materialId");
    
    if (!materialId) {
        alert("ID-ul materialului nu a fost găsit!");
        return;
    }

    const token = getCookie("access_token");
    if (!token) {
        alert("Nu ești autentificat!");
        return;
    }

    if (!confirm(`Sigur vrei să ștergi ${filename}?`)) {
        return;
    }

    try {
        // Encodează filename-ul pentru URL (în caz că are caractere speciale)
        const encodedFilename = encodeURIComponent(filename);
        const url = `/materials/material/${materialId}/file?filename=${encodedFilename}`;
        
        const response = await fetch(url, {
            method: "DELETE",
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            credentials: "include"
        });

        if (response.ok) {
            const data = await response.json();
            alert("Fișier șters cu succes!");
            location.reload();
        } 
        else {
            const errorData = await response.json();
            alert(`Eroare: ${errorData.detail}`);
        }
    } catch (err) {
        console.error("Exception during delete:", err);
        alert("Eroare la ștergere: " + err.message);
    }
}

function getAuthHeaders() {
  const token = getCookie("access_token");
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
}

async function approveUser(userId, btn) {
  try {
    const res = await fetch(`/users/${userId}/approve`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      credentials: "same-origin"
    });
    
    if (res.ok) {
      const data = await res.json();
      console.log("✅ User approved:", data);
      location.reload();
    } else {
      const data = await res.json();
      alert(data.detail || "Could not approve user");
    }
  } catch (err) {
    console.error("Error approving user:", err);
    alert("Eroare la aprobare: " + err.message);
  }
}

async function dismissUser(userId, btn) {
  if (!confirm("Sigur vrei să ștergi acest utilizator?")) {
    return;
  }
  
  try {
    const res = await fetch(`/users/${userId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
      credentials: "same-origin"
    });
    
    if (res.ok) {
      const data = await res.json();
      console.log("✅ User dismissed:", data);
      document.getElementById(`user-row-${userId}`).remove();
    } else {
      const data = await res.json();
      alert(data.detail || "Could not dismiss user");
    }
  } catch (err) {
    console.error("Error dismissing user:", err);
    alert("Eroare la ștergere: " + err.message);
  }
}

async function revokeApproval(userId, btn) {
  try {
    const res = await fetch(`/users/${userId}/revoke`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      credentials: "same-origin"
    });
    
    if (res.ok) {
      const data = await res.json();
      console.log("✅ Approval revoked:", data);
      location.reload();
    } else {
      const data = await res.json();
      alert(data.detail || "Could not revoke approval");
    }
  } catch (err) {
    console.error("Error revoking approval:", err);
    alert("Eroare la revocare: " + err.message);
  }
}