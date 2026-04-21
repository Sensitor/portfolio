public class VoieDeLaResistance extends Voie {
    public VoieDeLaResistance() {
        super("Voie de la resistance");
        competences.add(new Competence("Robustesse", 1));
        competences.add(new Competence("Armure naturelle", 2));
        competences.add(new Competence("Second souffle", 3));
        competences.add(new Competence("Dur a cuire", 4));
    }
}
