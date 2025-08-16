import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getDatabase, ref, get, set } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-database.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-auth.js";
import { getStorage, ref as storageRef, uploadBytes, getDownloadURL } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-storage.js";

// Firebase initialization
const firebaseConfig = window.firebaseConfig;
const app = initializeApp(firebaseConfig);
const database = getDatabase(app);
const auth = getAuth(app);
const storage = getStorage(app);

// Utility functions
function encodeBarCouncilID(barCouncilID) {
    return barCouncilID.replace(/[^a-zA-Z0-9]/g, "_"); 
}

function decodeBarCouncilID(encodedID) {
    return encodedID.replace(/_/g, "/");
}

// DOM Elements
const profilePicElement = document.getElementById("profilePic");
const profilePicInputElement = document.getElementById("profilePicInput");
const editProfileModal = document.getElementById("editProfileModal");
const editProfileForm = document.getElementById("editProfileForm");
const logoutButton = document.getElementById("logout");

// Main Profile Loading Functionality
function loadProfileData(userId) {
    return new Promise((resolve, reject) => {
        const lawyerRef = ref(database, `lawyers/${userId}`);

        get(lawyerRef).then((snapshot) => {
            if (snapshot.exists()) {
                const lawyerData = snapshot.val();
                console.log("Lawyer Basic Data:", lawyerData);

                // Populate immutable fields
                document.getElementById("lawyername").value = lawyerData.name;
                document.getElementById("lawyerName").innerText = lawyerData.name;
                document.getElementById("lawyerEmail").innerText = lawyerData.email;
                document.getElementById("barCouncilID").innerText = lawyerData.barCouncilID;

                resolve(lawyerData.barCouncilID);
            } else {
                console.log("No lawyer data found.");
                reject("No lawyer data found");
            }
        }).catch((error) => {
            console.error("Error fetching lawyer data:", error);
            reject(error);
        });
    });
}

function loadLawyerProfile(barCouncilID) {
    const encodedBarCouncilID = encodeBarCouncilID(barCouncilID);
    const profileRef = ref(database, `lawyers_profile/lawyer_profile/${encodedBarCouncilID}`);

    get(profileRef).then((snapshot) => {
        if (snapshot.exists()) {
            const profileData = snapshot.val();
            console.log("Profile Data:", profileData);

            // Map to display fields with strict field names
            const displayData = {
                contact: profileData.contact || "Not Provided",
                address: profileData.Location || "Not Provided",
                firmName: profileData.Firm_name || "Not Provided",
                firmSize: profileData.Firm_size || "Not Provided",
                affiliation: profileData.Affiliation || "Not Provided",
                practiceArea: profileData.Practice_area || "Not Provided",
                designation: profileData.Designation || "Not Provided",
                experience: profileData.Years_of_Experience || "Not Provided",
                cases: profileData.Successful_cases || "Not Provided",
                fees: profileData.Nominal_fees_per_hearing || "Not Provided",
                Total_cases: profileData.Total_cases || "Not Provided" // Add this line
            };

            updateDisplayFields(displayData);

            // Update form fields
            document.getElementById("contact").value = displayData.contact;
            document.getElementById("address").value = displayData.address;
            document.getElementById("firmName").value = displayData.firmName;
            document.getElementById("firmSize").value = displayData.firmSize;
            document.getElementById("affiliation").value = displayData.affiliation;
            document.getElementById("practiceArea").value = displayData.practiceArea;
            document.getElementById("designation").value = displayData.designation;
            document.getElementById("experience").value = displayData.experience;
            document.getElementById("totalCases").value = displayData.Total_cases; // Add this line
            document.getElementById("cases").value = displayData.cases;
            document.getElementById("fees").value = displayData.fees;

            // Update profile picture if available
            if (profileData.profilePicUrl) {
                profilePicElement.src = profileData.profilePicUrl;
            }
        } else {
            console.log("No profile data found for this lawyer.");
            updateDisplayFields({
                contact: "Not Provided",
                address: "Not Provided",
                firmName: "Not Provided",
                firmSize: "Not Provided",
                affiliation: "Not Provided",
                practiceArea: "Not Provided",
                designation: "Not Provided",
                experience: "Not Provided",
                cases: "Not Provided",
                fees: "Not Provided",
                Total_cases: "Not Provided" // Add this line
            });
        }
    }).catch(error => console.error("Error fetching profile data:", error));
}

function updateDisplayFields(data) {
    const fieldMap = {
        contact: "displayContact",
        address: "displayAddress",
        firmName: "displayFirmName",
        firmSize: "displayFirmSize",
        affiliation: "displayAffiliation",
        practiceArea: "displayPracticeArea",
        designation: "displayDesignation",
        experience: "displayExperience",
        cases: "displayCases",
        fees: "displayFees",
        Total_cases: "displayTotalCases" // Add this line
    };

    for (const [dataKey, elementId] of Object.entries(fieldMap)) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = data[dataKey] || "Not Provided";
        }
    }
    
    // Calculate success rate after updating fields
    setTimeout(calculateSuccessRate, 500);
}

// Profile Modal Functions
window.openEditProfile = function() {
    document.getElementById("contact").value = document.getElementById("displayContact").textContent;
    document.getElementById("address").value = document.getElementById("displayAddress").textContent;
    document.getElementById("firmName").value = document.getElementById("displayFirmName").textContent;
    document.getElementById("firmSize").value = document.getElementById("displayFirmSize").textContent;
    document.getElementById("affiliation").value = document.getElementById("displayAffiliation").textContent;
    document.getElementById("practiceArea").value = document.getElementById("displayPracticeArea").textContent;
    document.getElementById("designation").value = document.getElementById("displayDesignation").textContent;
    document.getElementById("experience").value = document.getElementById("displayExperience").textContent;
    document.getElementById("cases").value = document.getElementById("displayCases").textContent;
    document.getElementById("fees").value = document.getElementById("displayFees").textContent;
    
    editProfileModal.style.display = "flex";
};

window.closeEditProfile = function() {
    editProfileModal.style.display = "none";
};

// Form Submission Handler with Strict Field Formatting
editProfileForm.addEventListener("submit", function(event) {
    event.preventDefault();

    const user = auth.currentUser;
    if (!user) {
        alert("User not authenticated!");
        return;
    }

    const lawyerRef = ref(database, `lawyers/${user.uid}`);
    get(lawyerRef).then((snapshot) => {
        if (snapshot.exists()) {
            const lawyerData = snapshot.val();
            const barCouncilID = lawyerData.barCouncilID;
            const encodedBarCouncilID = encodeBarCouncilID(barCouncilID);

            // Prepare data with EXACT field names as specified
            const profileData = {
                Lawyer_name: document.getElementById("lawyername").value,
                Practice_area: document.getElementById("practiceArea").value || "Not Specified",
                Firm_name: document.getElementById("firmName").value || "Not Specified",
                Firm_size: parseInt(document.getElementById("firmSize").value) || "Not Specified",
                Target_audience: "General Public",
                Designation: document.getElementById("designation").value || "Not Specified",
                Years_of_Experience: parseInt(document.getElementById("experience").value) || 0,
                Total_cases: parseInt(document.getElementById("totalCases").value) || 0, // Added this line
                Successful_cases: parseInt(document.getElementById("cases").value) || 0,
                Affiliation: document.getElementById("affiliation").value || "Not Specified",
                Client_reviews: "No reviews yet",
                Nominal_fees_per_hearing: parseInt(document.getElementById("fees").value) || 0,
                Bar_Council_ID: barCouncilID,
                sentiment_score: 0.75,
                Location: document.getElementById("address").value || "Not Specified",
                
                // Additional fields for internal use
                contact: document.getElementById("contact").value,
                profilePicUrl: document.getElementById("profilePic").src
            };

            // Update display
            updateDisplayFields({
                contact: profileData.contact,
                address: profileData.Location,
                firmName: profileData.Firm_name,
                firmSize: profileData.Firm_size,
                affiliation: profileData.Affiliation,
                practiceArea: profileData.Practice_area,
                designation: profileData.Designation,
                experience: profileData.Years_of_Experience,
                cases: profileData.Successful_cases,
                fees: profileData.Nominal_fees_per_hearing,
                Total_cases: profileData.Total_cases // Add this line
            });

            // Save with EXACT field names
            const profileRef = ref(database, `lawyers_profile/lawyer_profile/${encodedBarCouncilID}`);
            set(profileRef, profileData)
                .then(() => {
                    closeEditProfile();
                    showProfileUpdateSuccessModal();
                })
                .catch(error => {
                    console.error("Error updating profile:", error);
                    alert("Error updating profile. Please try again.");
                });
        }
    }).catch(error => {
        console.error("Error fetching lawyer data:", error);
        alert("Error updating profile. Please try again.");
    });
});

// Profile Picture Upload
profilePicElement.addEventListener("click", function() {
    profilePicInputElement.click();
});

profilePicInputElement.addEventListener("change", function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const user = auth.currentUser;
    if (!user) {
        alert("User not authenticated!");
        return;
    }

    const lawyerRef = ref(database, `lawyers/${user.uid}`);
    get(lawyerRef).then((snapshot) => {
        if (snapshot.exists()) {
            const lawyerData = snapshot.val();
            const barCouncilID = lawyerData.barCouncilID;
            const encodedBarCouncilID = encodeBarCouncilID(barCouncilID);

            const storageReference = storageRef(storage, `lawyers_profile/lawyer_profile/${encodedBarCouncilID}/profilePic.jpg`);
            uploadBytes(storageReference, file)
                .then(() => getDownloadURL(storageReference))
                .then(url => {
                    profilePicElement.src = url;
                    return update(ref(database, `lawyers_profile/lawyer_profile/${encodedBarCouncilID}`), { 
                        profilePicUrl: url 
                    });
                })
                .then(() => alert("Profile picture updated!"))
                .catch(error => {
                    console.error("Error updating profile picture:", error);
                    alert("Error updating profile picture. Please try again.");
                });
        }
    }).catch(error => {
        console.error("Error fetching lawyer data:", error);
        alert("Error updating profile picture. Please try again.");
    });
});

// Logout Functionality with proper redirection
logoutButton.addEventListener("click", function () {
    document.getElementById("logoutModal")?.classList.add("show");
    document.getElementById("logoutModalClose")?.addEventListener("click", function () {
        signOut(auth).then(() => {
            document.getElementById("logoutModal")?.classList.remove("show");
            window.location.href = "/";
        }).catch((error) => {
            console.error("Logout error:", error);
            alert("Error during logout. Please try again.");
        });
    });
});


// Initialize the page with proper authentication handling
// Initialize the page with proper authentication handling
onAuthStateChanged(auth, (user) => {
    if (user) {
        loadProfileData(user.uid)
            .then(barCouncilID => loadLawyerProfile(barCouncilID))
            .catch(error => {
                console.error("Error loading profile:", error);
                window.location.href = "/";
            });
    } else {
        // Redirect to home page if not authenticated
        window.location.href = "/";
    }
});

// ✅ Show welcome modal once per session
document.addEventListener("DOMContentLoaded", function () {
    const welcomeModal = document.getElementById("welcomeModal");
    const closeBtn = document.getElementById("welcomeModalClose");

    if (!sessionStorage.getItem("welcomeShown") && welcomeModal) {
        welcomeModal.classList.add("show");
        sessionStorage.setItem("welcomeShown", "true");
    }

    closeBtn?.addEventListener("click", () => {
        welcomeModal.classList.remove("show");
    });

    // Profile updated modal close
    const profileUpdatedClose = document.getElementById("profileUpdatedModalClose");
    profileUpdatedClose?.addEventListener("click", () => {
        document.getElementById("profileUpdatedModal")?.classList.remove("show");
    });
});
