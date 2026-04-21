public class VoieDuTraqueur extends Voie {
    public VoieDuTraqueur() {
        super("Voie du traqueur");
        competences.add(new Competence("Pas de loup", 1));
        competences.add(new Competence("Ennemi jure", 2));
        competences.add(new Competence("Embuscade", 3));
        competences.add(new Competence("Second ennemi jure", 4));
    }
}
