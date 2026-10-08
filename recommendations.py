from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_user_recommendations(materials, user, current_material=None, limit=4):
    if not materials:
        return []

    # Build the user's interest profile
    user_profile_parts = []

    if user and user.department:
        user_profile_parts.append(user.department)

    if user:
        for loan in user.loans:
            if loan.material:
                if loan.material.subject:
                    user_profile_parts.append(loan.material.subject)

                if loan.material.title:
                    user_profile_parts.append(loan.material.title)

    user_profile = " ".join(user_profile_parts)

    # If the user has no useful profile, fall back to the
    # content of the material currently being viewed.
    if not user_profile.strip() and current_material:
        user_profile = " ".join([
            current_material.title or "",
            current_material.subject or "",
            current_material.description or "",
            current_material.author or ""
        ])

    documents = []

    for material in materials:
        text = " ".join([
            material.title or "",
            material.subject or "",
            material.description or "",
            material.author or ""
        ])

        documents.append(text)

    # Add the user/current-book profile
    documents.append(user_profile)

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    profile_vector = tfidf_matrix[-1]
    material_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(
        profile_vector,
        material_vectors
    )[0]

    ranked_indices = similarities.argsort()[::-1]

    borrowed_ids = set()

    if user:
        borrowed_ids = {
            loan.material_id
            for loan in user.loans
        }

    recommendations = []

    for index in ranked_indices:
        material = materials[index]

        # Don't recommend the material currently being viewed
        if current_material and material.id == current_material.id:
            continue

        # Don't recommend something the patron already borrowed
        if material.id in borrowed_ids:
            continue

        recommendations.append(material)

        if len(recommendations) >= limit:
            break

    return recommendations