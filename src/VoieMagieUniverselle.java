public class VoieMagieUniverselle extends Voie {
    public VoieMagieUniverselle() {
        super("Voie de la magie universelle");
        competences.add(new Competence("Lumiere", 1));
        competences.add(new Competence("Detection de la magie", 2));
        competences.add(new Competence("Invisibilite", 3));
        competences.add(new Competence("Vol", 4));
    }
}
